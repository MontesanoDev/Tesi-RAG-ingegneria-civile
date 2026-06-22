import shutil
from pathlib import Path

import chainlit as cl

from src.generation.checklist_generator import generate_checklist, save_checklist
from src.indexing.index_builder import DEFAULT_DATA_DIR, build_or_update_index
from src.retrieval.rag_engine import RagEngine


HELP_TEXT = """Demo MVP per analisi di un bando.

Comandi disponibili:
- `/index` costruisce o aggiorna l'indice locale dai PDF in `data/bandi/`
- `/checklist` genera una checklist operativa revisionabile
- `/save` salva l'ultima checklist in `outputs/checklist/`
- `/bando percorso/file.pdf` copia manualmente un PDF in `data/bandi/`
- profilo aziendale letto, se presente, da `data/aziende/mapi_ingegneria.yaml`
- una domanda libera interroga il bando tramite RAG
"""


def _ensure_data_dir() -> None:
    DEFAULT_DATA_DIR.mkdir(parents=True, exist_ok=True)


def _copy_pdf_to_bandi(source_path: str | Path) -> Path:
    source = Path(source_path)
    if not source.exists():
        raise FileNotFoundError(f"PDF non trovato: {source}")
    if source.suffix.lower() != ".pdf":
        raise ValueError("Il file selezionato non e' un PDF.")

    _ensure_data_dir()
    destination = DEFAULT_DATA_DIR / source.name
    if source.resolve() != destination.resolve():
        shutil.copy2(source, destination)
    return destination


async def _copy_message_uploads(message: cl.Message) -> list[Path]:
    copied: list[Path] = []
    for element in message.elements or []:
        path = getattr(element, "path", None)
        name = getattr(element, "name", "")
        if not path or not name.lower().endswith(".pdf"):
            continue
        copied.append(_copy_pdf_to_bandi(path))
    return copied


def _get_engine() -> RagEngine:
    engine = cl.user_session.get("rag_engine")
    if engine is None:
        engine = RagEngine()
        cl.user_session.set("rag_engine", engine)
    return engine


async def _send_sources(sources: list[dict]) -> None:
    if not sources:
        await cl.Message(
            content="**Fonti:** nessuna fonte recuperata dall'indice."
        ).send()
        return

    lines = ["**Fonti recuperate:**"]
    for source in sources[:8]:
        score = source.get("score")
        score_text = f" - rilevanza {score * 100:.1f}%" if score is not None else ""
        lines.append(f"- {source.get('source', 'Fonte sconosciuta')}{score_text}")
    await cl.Message(content="\n".join(lines)).send()


async def _send_status(content: str, author: str) -> cl.Message:
    msg = cl.Message(content=content, author=author)
    await msg.send()
    return msg


async def _update_message(message: cl.Message, content: str) -> None:
    message.content = content
    await message.update()


@cl.on_chat_start
async def start():
    _ensure_data_dir()
    cl.user_session.set("last_checklist", None)
    await cl.Message(content=HELP_TEXT).send()

    try:
        files = await cl.AskFileMessage(
            content="Carica un PDF del bando, oppure usa `/bando percorso/file.pdf`.",
            accept=["application/pdf"],
            max_size_mb=30,
            timeout=60,
        ).send()
    except TimeoutError:
        files = []

    if files:
        copied = [_copy_pdf_to_bandi(file.path) for file in files]
        names = ", ".join(path.name for path in copied)
        await cl.Message(
            content=f"PDF copiato in `data/bandi/`: {names}\nEsegui `/index` per costruire l'indice."
        ).send()


@cl.on_message
async def main(message: cl.Message):
    uploaded = await _copy_message_uploads(message)
    if uploaded:
        names = ", ".join(path.name for path in uploaded)
        await cl.Message(
            content=f"PDF copiato in `data/bandi/`: {names}\nEsegui `/index` per aggiornare l'indice."
        ).send()
        return

    content = (message.content or "").strip()
    if not content:
        await cl.Message(content="Query vuota. Inserisci una domanda o un comando.").send()
        return

    if content == "/help":
        await cl.Message(content=HELP_TEXT).send()
        return

    if content.startswith("/bando "):
        try:
            copied = _copy_pdf_to_bandi(content.removeprefix("/bando ").strip())
            cl.user_session.set("rag_engine", None)
            await cl.Message(
                content=f"PDF selezionato: `{copied}`\nEsegui `/index` per costruire l'indice."
            ).send()
        except Exception as exc:
            await cl.Message(content=f"Errore nella selezione del PDF: {exc}").send()
        return

    if content == "/index":
        status_msg = await _send_status(
            "Indicizzazione in corso: leggo i PDF, genero gli embeddings e aggiorno ChromaDB...",
            author="Indice",
        )
        try:
            result = await cl.make_async(build_or_update_index)()
            cl.user_session.set("rag_engine", None)
            await _update_message(
                status_msg,
                (
                    f"{result['message']}\n"
                    f"- PDF: {result['pdf_count']}\n"
                    f"- Chunk indicizzati: {result['chunks']}\n"
                    f"- Collection: `{result['collection']}`"
                ),
            )
        except Exception as exc:
            await _update_message(
                status_msg,
                f"Errore durante l'indicizzazione: {exc}",
            )
        return

    if content == "/checklist":
        status_msg = await _send_status(
            "Sto generando la checklist: recupero i requisiti del bando e preparo il Markdown...",
            author="Checklist",
        )
        try:
            engine = RagEngine(similarity_top_k=12, streaming=False)
            result = await cl.make_async(generate_checklist)(engine)
            markdown = result["markdown"]
            cl.user_session.set("last_checklist", markdown)
            await _update_message(status_msg, markdown)
            if not result["company_profile_loaded"]:
                await cl.Message(
                    content=(
                        "Profilo aziendale non trovato in "
                        "`data/aziende/mapi_ingegneria.yaml`: "
                        "la sezione sulle informazioni aziendali andra' verificata manualmente."
                    )
                ).send()
            await _send_sources(result["sources"])
        except Exception as exc:
            await _update_message(
                status_msg,
                f"Errore nella generazione checklist: {exc}",
            )
        return

    if content == "/save":
        checklist = cl.user_session.get("last_checklist")
        if not checklist:
            await cl.Message(
                content="Nessuna checklist da salvare. Generala prima con `/checklist`."
            ).send()
            return
        try:
            path = save_checklist(checklist)
            await cl.Message(content=f"Checklist salvata in `{path}`.").send()
        except Exception as exc:
            await cl.Message(content=f"Errore durante il salvataggio: {exc}").send()
        return

    status_msg = await _send_status(
        "Sto recuperando i passaggi rilevanti dal bando e preparando la risposta...",
        author="RAG",
    )
    try:
        engine = _get_engine()
        result = await cl.make_async(engine.query)(content)
        response = result["response"]
        status_msg.content = ""
        await status_msg.update()
        for token in response.response_gen:
            await status_msg.stream_token(token)
        await status_msg.update()
        await _send_sources(result["sources"])
    except Exception as exc:
        await _update_message(status_msg, f"Errore nella query: {exc}")

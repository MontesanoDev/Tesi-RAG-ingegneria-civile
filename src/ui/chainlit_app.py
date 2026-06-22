import asyncio
from contextlib import suppress
import re
import shutil
from pathlib import Path

import chainlit as cl

from src.extraction.bando_facts_extractor import (
    extract_bando_facts,
    render_facts_debug,
)
from src.generation.company_profile import load_company_profile
from src.generation.checklist_generator import (
    generate_checklist,
    save_checklist,
)
from src.generation.fact_qa_generator import answer_document_question_from_facts
from src.generation.summary_generator import generate_bando_summary
from src.indexing.index_builder import DEFAULT_DATA_DIR, build_or_update_index
from src.retrieval.rag_engine import RagEngine
from src.routing.fact_topic_router import classify_fact_topic
from src.routing.intent_router import Intent, classify_intent
from src.source_display import normalize_visible_sources


HELP_TEXT = """Demo MVP per analisi di un bando.

Comandi disponibili:
- `/index` costruisce o aggiorna l'indice locale dai PDF in `data/bandi/`
- `/checklist` genera una checklist operativa revisionabile
- `/facts` mostra i fatti estratti dal bando in formato debug
- `/save` salva l'ultima checklist in `outputs/checklist/`
- `/bando percorso/file.pdf` copia manualmente un PDF in `data/bandi/`
- puoi anche allegare un PDF in chat quando vuoi, senza obbligo all'avvio
- profilo aziendale letto, se presente, da `data/aziende/mapi_ingegneria.yaml`
- puoi chiedere "riassumi il bando" per una sintesi section-aware
- una domanda libera prova prima i fatti estratti e poi, se serve, il RAG
"""

TYPEWRITE_INTERVAL_SECONDS = 0.018
TYPEWRITE_MAX_SECONDS = 2.4
TYPEWRITE_MIN_CHUNK_SIZE = 24
SOURCE_PAGE_RE = re.compile(r"pag\.\s*(\d+)", re.IGNORECASE)
GREETING_REPLY = (
    "Ciao! Puoi chiedermi un riassunto del bando, generare `/checklist`, "
    "fare domande sui requisiti oppure chiedere informazioni su MAPI Ingegneria."
)
HELP_REPLY = (
    "Puoi chiedermi un riassunto del bando, generare una checklist con `/checklist`, "
    "fare domande sui requisiti oppure chiedere informazioni su MAPI Ingegneria."
)


def _ensure_data_dir() -> None:
    DEFAULT_DATA_DIR.mkdir(parents=True, exist_ok=True)


def _loaded_pdf_names() -> list[str]:
    if not DEFAULT_DATA_DIR.exists():
        return []
    return [path.name for path in sorted(DEFAULT_DATA_DIR.glob("*.pdf"))]


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


async def _get_engine_async() -> RagEngine:
    engine = cl.user_session.get("rag_engine")
    if engine is None:
        engine = await cl.make_async(RagEngine)()
        cl.user_session.set("rag_engine", engine)
    return engine


def _run_checklist_command() -> dict:
    engine = RagEngine(similarity_top_k=8, streaming=False, build_query_engine=False)
    return generate_checklist(engine)


def _run_summary_command() -> dict:
    engine = RagEngine(similarity_top_k=8, streaming=False, build_query_engine=False)
    return generate_bando_summary(engine)


def _run_facts_command() -> dict:
    engine = RagEngine(similarity_top_k=8, streaming=False, build_query_engine=False)
    facts = extract_bando_facts(
        engine,
        debug_label="FACTS DEBUG",
        intent="facts",
    )
    return {
        "markdown": render_facts_debug(facts),
        "sources": facts.sources,
    }


def _run_fact_qa_command(content: str) -> dict | None:
    engine = RagEngine(similarity_top_k=8, streaming=False, build_query_engine=False)
    facts = extract_bando_facts(engine)
    return answer_document_question_from_facts(content, facts)


def _print_qa_debug(topic: str | None, source: str, fallback_to_rag: bool) -> None:
    print("[QA DEBUG]")
    print("intent: document_qa")
    print(f"topic: {topic or 'none'}")
    print(f"source: {source}")
    print(f"fallback_to_rag: {'yes' if fallback_to_rag else 'no'}")


def _company_profile_reply() -> str:
    profile = load_company_profile()
    if not profile:
        return (
            "Non trovo un profilo aziendale in `data/aziende/mapi_ingegneria.yaml`. "
            "Posso comunque rispondere sul bando caricato o generare `/checklist`."
        )

    return (
        "Se stai chiedendo del profilo aziendale caricato: sei "
        "**MAPI Ingegneria S.r.l.**, una PMI con sede in Puglia che opera in "
        "ingegneria civile, infrastrutture e progettazione tecnica. Nel profilo risultano "
        "attivita' come progettazione di opere pubbliche, direzione lavori, consulenza "
        "tecnica, gestione pratiche autorizzative e supporto a enti pubblici e privati. "
        "Restano da verificare dati come fatturato, numero dipendenti, certificazioni "
        "effettive, referenze documentabili e curriculum tecnico."
    )


async def _send_sources(sources: list[dict]) -> None:
    if not sources:
        await cl.Message(
            content="**Fonti:** nessuna fonte recuperata dall'indice."
        ).send()
        return

    lines = ["**Fonti recuperate:**"]
    display_sources: list[tuple[int, str]] = []
    seen: set[str] = set()

    for source in sources:
        source_text = normalize_visible_sources(source.get("source", "Fonte sconosciuta"))
        if source_text in seen:
            continue
        seen.add(source_text)

        page = source.get("page")
        if page is None:
            match = SOURCE_PAGE_RE.search(source_text)
            page = int(match.group(1)) if match else 10**9
        try:
            page_number = int(page)
        except (TypeError, ValueError):
            page_number = 10**9
        display_sources.append((page_number, source_text))

    for _, source_text in sorted(display_sources, key=lambda item: item[0])[:12]:
        lines.append(f"- {source_text}")
    await cl.Message(content="\n".join(lines)).send()


async def _send_status(content: str, author: str) -> cl.Message:
    msg = cl.Message(content=content, author=author)
    await msg.send()
    return msg


def _thinking_content(label: str, detail: str) -> str:
    return f"> **{label}**\n> {detail}"


async def _animate_status(
    message: cl.Message,
    label: str,
    details: tuple[str, ...],
    interval: float = 1.0,
) -> None:
    index = 0
    while True:
        detail = details[index % len(details)]
        message.content = _thinking_content(label, detail)
        await message.update()
        index += 1
        await asyncio.sleep(interval)


async def _stop_animation(task: asyncio.Task | None) -> None:
    if task is None:
        return
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


async def _update_message(message: cl.Message, content: str) -> None:
    message.content = content
    await message.update()


async def _reveal_message(
    message: cl.Message,
    content: str,
    interval: float = TYPEWRITE_INTERVAL_SECONDS,
    max_seconds: float = TYPEWRITE_MAX_SECONDS,
) -> None:
    if not content:
        await _update_message(message, "")
        return

    max_steps = max(1, int(max_seconds / interval))
    chunk_size = max(
        TYPEWRITE_MIN_CHUNK_SIZE,
        (len(content) + max_steps - 1) // max_steps,
    )

    for end in range(chunk_size, len(content) + chunk_size, chunk_size):
        message.content = content[:end]
        await message.update()
        await asyncio.sleep(interval)

    if message.content != content:
        await _update_message(message, content)


async def _send_revealed(content: str, author: str = "Assistant") -> None:
    message = cl.Message(content="", author=author)
    await message.send()
    await _reveal_message(message, content)


@cl.on_chat_start
async def start():
    _ensure_data_dir()
    cl.user_session.set("last_checklist", None)
    await cl.Message(content=HELP_TEXT).send()

    pdf_names = _loaded_pdf_names()
    if pdf_names:
        names = ", ".join(pdf_names)
        await cl.Message(
            content=(
                f"PDF gia' presenti in `data/bandi/`: {names}\n"
                "Puoi fare una domanda, usare `/checklist`, oppure `/index` se hai cambiato i file."
            )
        ).send()
    else:
        await cl.Message(
            content=(
                "Nessun PDF presente in `data/bandi/`. Puoi comunque scrivere un messaggio; "
                "quando vuoi, allega un PDF o usa `/bando percorso/file.pdf`."
            )
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
        await _send_revealed(HELP_REPLY)
        return

    if content == "/help":
        await _send_revealed(HELP_TEXT)
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

    intent = classify_intent(content)

    if content == "/index":
        status_msg = await _send_status(
            _thinking_content("Indicizzazione in corso", "Leggo i PDF e preparo i chunk."),
            author="Indice",
        )
        animation = asyncio.create_task(
            _animate_status(
                status_msg,
                "Indicizzazione in corso",
                (
                    "Leggo i PDF in `data/bandi/`...",
                    "Estraggo testo e metadati pagina per pagina...",
                    "Genero embeddings e aggiorno ChromaDB...",
                    "Scrivo manifest e controllo la collection...",
                ),
            )
        )
        await asyncio.sleep(0)
        try:
            result = await cl.make_async(build_or_update_index)()
            cl.user_session.set("rag_engine", None)
            await _stop_animation(animation)
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
            await _stop_animation(animation)
            await _update_message(
                status_msg,
                f"Errore durante l'indicizzazione: {exc}",
            )
        return

    if content == "/facts":
        status_msg = await _send_status(
            _thinking_content(
                "Facts in estrazione",
                "Recupero i campi principali del bando.",
            ),
            author="Facts",
        )
        animation = asyncio.create_task(
            _animate_status(
                status_msg,
                "Facts in estrazione",
                (
                    "Recupero oggetto, finalita' e dotazione...",
                    "Cerco soggetti, requisiti e scadenze...",
                    "Raccolgo documenti, criteri e obblighi...",
                    "Preparo il riepilogo debug dei fatti estratti...",
                ),
            )
        )
        await asyncio.sleep(0)
        try:
            result = await cl.make_async(_run_facts_command)()
            markdown = normalize_visible_sources(result["markdown"])
            await _stop_animation(animation)
            await _reveal_message(status_msg, markdown)
            await _send_sources(result["sources"])
        except Exception as exc:
            await _stop_animation(animation)
            await _update_message(status_msg, f"Errore nell'estrazione facts: {exc}")
        return

    if intent == Intent.GREETING:
        await _send_revealed(GREETING_REPLY)
        return

    if intent == Intent.COMPANY_PROFILE:
        await _send_revealed(_company_profile_reply())
        return

    if intent == Intent.CHECKLIST:
        status_msg = await _send_status(
            _thinking_content(
                "Checklist in generazione",
                "Recupero le sezioni principali del bando.",
            ),
            author="Checklist",
        )
        animation = asyncio.create_task(
            _animate_status(
                status_msg,
                "Checklist in generazione",
                (
                    "Recupero soggetti ammessi e requisiti...",
                    "Cerco termini e modalita' di presentazione...",
                    "Raccolgo documentazione e allegati richiesti...",
                    "Separo candidatura, valutazione e post-concessione...",
                    "Compongo il Markdown finale con fonti leggibili...",
                ),
            )
        )
        await asyncio.sleep(0)
        try:
            result = await cl.make_async(_run_checklist_command)()
            markdown = normalize_visible_sources(result["markdown"])
            cl.user_session.set("last_checklist", markdown)
            await _stop_animation(animation)
            await _reveal_message(status_msg, markdown)
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
            await _stop_animation(animation)
            await _update_message(
                status_msg,
                f"Errore nella generazione checklist: {exc}",
            )
        return

    if intent == Intent.SUMMARY:
        status_msg = await _send_status(
            _thinking_content(
                "Riassunto in preparazione",
                "Recupero le sezioni principali del bando.",
            ),
            author="Riassunto",
        )
        animation = asyncio.create_task(
            _animate_status(
                status_msg,
                "Riassunto in preparazione",
                (
                    "Recupero finalita' e oggetto del bando...",
                    "Cerco requisiti e soggetti coinvolti...",
                    "Raccolgo termini, modalita' e documentazione...",
                    "Preparo una sintesi con fonti leggibili...",
                ),
            )
        )
        await asyncio.sleep(0)
        try:
            result = await cl.make_async(_run_summary_command)()
            markdown = normalize_visible_sources(result["markdown"])
            await _stop_animation(animation)
            await _reveal_message(status_msg, markdown)
            await _send_sources(result["sources"])
        except Exception as exc:
            await _stop_animation(animation)
            await _update_message(status_msg, f"Errore nella generazione riassunto: {exc}")
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

    if intent in {Intent.HELP, Intent.COMMAND}:
        await _send_revealed(HELP_REPLY)
        return

    if intent != Intent.DOCUMENT_QA:
        await _send_revealed(HELP_REPLY)
        return

    fact_topic = classify_fact_topic(content)
    if fact_topic is not None:
        status_msg = await _send_status(
            _thinking_content(
                "Facts in consultazione",
                "Controllo se la risposta e' gia' nei fatti estratti.",
            ),
            author="Facts",
        )
        animation = asyncio.create_task(
            _animate_status(
                status_msg,
                "Facts in consultazione",
                (
                    "Cerco il campo corrispondente nei BandoFacts...",
                    "Preparo una risposta breve con fonti leggibili...",
                    "Controllo se serve passare al RAG generico...",
                ),
            )
        )
        await asyncio.sleep(0)
        try:
            fact_result = await cl.make_async(_run_fact_qa_command)(content)
            await _stop_animation(animation)
            if fact_result:
                _print_qa_debug(fact_result["topic"], "BandoFacts", False)
                await _reveal_message(
                    status_msg,
                    normalize_visible_sources(fact_result["markdown"]),
                )
                await _send_sources(fact_result["sources"])
                return
            _print_qa_debug(fact_topic, "RAG", True)
            await _update_message(status_msg, "")
        except Exception:
            await _stop_animation(animation)
            _print_qa_debug(fact_topic, "RAG", True)
            await _update_message(status_msg, "")
    else:
        _print_qa_debug(None, "RAG", True)

    status_msg = await _send_status(
        _thinking_content("RAG al lavoro", "Recupero i passaggi rilevanti dal bando."),
        author="RAG",
    )
    animation = asyncio.create_task(
        _animate_status(
            status_msg,
            "RAG al lavoro",
            (
                "Recupero i chunk piu' pertinenti...",
                "Controllo le fonti e le pagine del bando...",
                "Preparo il contesto per il modello...",
                "Sto generando una risposta grounded...",
            ),
        )
    )
    await asyncio.sleep(0)
    try:
        engine = await _get_engine_async()
        result = await cl.make_async(engine.query)(content)
        response = result["response"]
        await _stop_animation(animation)
        status_msg.content = ""
        await status_msg.update()
        answer_parts = []
        for token in response.response_gen:
            answer_parts.append(token)
        await _reveal_message(
            status_msg,
            normalize_visible_sources("".join(answer_parts)),
        )
        await _send_sources(result["sources"])
    except Exception as exc:
        await _stop_animation(animation)
        await _update_message(status_msg, f"Errore nella query: {exc}")

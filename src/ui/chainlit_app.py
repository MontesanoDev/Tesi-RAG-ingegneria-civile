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
from src.generation.company_eligibility_generator import generate_company_eligibility
from src.generation.fact_qa_generator import answer_fact_topic
from src.generation.participation_steps_generator import generate_participation_steps
from src.generation.summary_generator import generate_bando_summary
from src.indexing.index_builder import DEFAULT_DATA_DIR, build_or_update_index
from src.retrieval.rag_engine import RagEngine
from src.routing.command_router import normalize_explicit_command
from src.routing.semantic_router import RouterDecision, classify_message, normalize_message
from src.source_display import display_name_for_file, normalize_visible_sources


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

COMPOSER_COMMANDS = [
    {
        "id": "index",
        "description": "Aggiorna l'indice locale dai PDF in data/bandi",
        "icon": "database",
        "button": False,
        "persistent": False,
        "selected": False,
    },
    {
        "id": "checklist",
        "description": "Genera la checklist operativa per la candidatura",
        "icon": "list-checks",
        "button": False,
        "persistent": False,
        "selected": False,
    },
    {
        "id": "facts",
        "description": "Mostra i fatti estratti dal bando",
        "icon": "file-search",
        "button": False,
        "persistent": False,
        "selected": False,
    },
    {
        "id": "summary",
        "description": "Genera un riassunto operativo del bando",
        "icon": "scroll-text",
        "button": False,
        "persistent": False,
        "selected": False,
    },
    {
        "id": "save",
        "description": "Salva l'ultima checklist generata",
        "icon": "save",
        "button": False,
        "persistent": False,
        "selected": False,
    },
    {
        "id": "checkpoint",
        "description": "Alias di save: salva il checkpoint operativo corrente",
        "icon": "bookmark",
        "button": False,
        "persistent": False,
        "selected": False,
    },
    {
        "id": "profile",
        "description": "Mostra il profilo MAPI Ingegneria",
        "icon": "building-2",
        "button": False,
        "persistent": False,
        "selected": False,
    },
    {
        "id": "bando",
        "description": "Aggiungi un PDF: /bando percorso/file.pdf",
        "icon": "file-plus-2",
        "button": False,
        "persistent": False,
        "selected": False,
    },
    {
        "id": "help",
        "description": "Mostra una guida breve",
        "icon": "circle-help",
        "button": False,
        "persistent": False,
        "selected": False,
    },
]

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
    display_names = [
        display_name_for_file(path.name) for path in sorted(DEFAULT_DATA_DIR.glob("*.pdf"))
    ]
    return sorted(dict.fromkeys(display_names))


async def _set_composer_commands() -> None:
    await cl.context.emitter.set_commands(COMPOSER_COMMANDS)


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


def _run_fact_qa_command(topic: str) -> dict | None:
    engine = RagEngine(similarity_top_k=8, streaming=False, build_query_engine=False)
    facts = extract_bando_facts(engine)
    return answer_fact_topic(topic, facts)


def _run_company_eligibility_command() -> dict:
    engine = RagEngine(similarity_top_k=8, streaming=False, build_query_engine=False)
    return generate_company_eligibility(engine)


def _run_participation_steps_command() -> dict:
    engine = RagEngine(similarity_top_k=8, streaming=False, build_query_engine=False)
    return generate_participation_steps(engine)


def _print_router_debug(
    message: str,
    command: str | None,
    decision: RouterDecision | None,
    fact_topic: str | None,
    source: str,
    fallback_to_rag: bool = False,
) -> None:
    print("[ROUTER DEBUG]")
    print(f"message: {message}")
    print(f"normalized: {normalize_message(message)}")
    print(f"command: {command or 'none'}")
    print(f"intent: {decision.intent if decision else 'none'}")
    print(f"fact_topic: {fact_topic or (decision.fact_topic if decision else 'none')}")
    print(f"confidence: {decision.confidence:.2f}" if decision else "confidence: 0.00")
    print(f"source: {source}")
    print(f"fallback_to_rag: {'yes' if fallback_to_rag else 'no'}")


def _print_qa_debug(
    message: str,
    topic: str | None,
    source: str,
    fallback_to_rag: bool,
    intent: str = "fact_qa",
) -> None:
    print("[QA DEBUG]")
    print(f"message: {message}")
    print(f"intent: {intent}")
    print(f"fact_topic: {topic or 'none'}")
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


async def dispatch_command(command: str) -> bool:
    if command == "/help":
        await _send_revealed(HELP_TEXT)
        return True

    if command == "/bando":
        await _send_revealed("Uso: `/bando percorso/file.pdf`")
        return True

    if command.startswith("/bando "):
        try:
            copied = _copy_pdf_to_bandi(command.removeprefix("/bando ").strip())
            cl.user_session.set("rag_engine", None)
            display_name = display_name_for_file(copied.name)
            await cl.Message(
                content=(
                    f"PDF selezionato: **{display_name}**\n"
                    "Esegui `/index` per costruire l'indice."
                )
            ).send()
        except Exception as exc:
            await cl.Message(content=f"Errore nella selezione del PDF: {exc}").send()
        return True

    if command == "/index":
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
        return True

    if command == "/facts":
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
        return True

    if command == "/checklist":
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
        return True

    if command == "/summary":
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
        return True

    if command == "/save":
        checklist = cl.user_session.get("last_checklist")
        if not checklist:
            await cl.Message(
                content="Nessuna checklist da salvare. Generala prima con `/checklist`."
            ).send()
            return True
        try:
            path = save_checklist(checklist)
            await cl.Message(content=f"Checklist salvata in `{path}`.").send()
        except Exception as exc:
            await cl.Message(content=f"Errore durante il salvataggio: {exc}").send()
        return True

    if command == "/azienda":
        await _send_revealed(_company_profile_reply())
        return True

    if command == "/status":
        pdf_names = _loaded_pdf_names()
        pdf_text = ", ".join(pdf_names) if pdf_names else "nessun PDF caricato"
        await _send_revealed(
            "Stato demo:\n"
            f"- PDF in `data/bandi/`: {pdf_text}\n"
            "- Usa `/index` dopo modifiche ai documenti.\n"
            "- Usa `/facts`, `/summary` o `/checklist` per gli output operativi."
        )
        return True

    return False


@cl.on_chat_start
async def start():
    _ensure_data_dir()
    cl.user_session.set("last_checklist", None)
    await _set_composer_commands()


@cl.on_message
async def main(message: cl.Message):
    uploaded = await _copy_message_uploads(message)
    if uploaded:
        names = ", ".join(display_name_for_file(path.name) for path in uploaded)
        await cl.Message(
            content=f"PDF copiato in `data/bandi/`: {names}\nEsegui `/index` per aggiornare l'indice."
        ).send()
        return

    raw_content = (message.content or "").strip()
    command = normalize_explicit_command(raw_content, getattr(message, "command", None))
    if command:
        _print_router_debug(raw_content, command, None, None, "command")
        if await dispatch_command(command):
            return

    content = raw_content
    if not content:
        decision = RouterDecision(
            intent="help",
            fact_topic="none",
            confidence=0.0,
            reason="Messaggio vuoto.",
        )
        _print_router_debug(raw_content, None, decision, None, "help")
        await _send_revealed(HELP_REPLY)
        return

    decision = classify_message(content)

    if decision.intent == "greeting":
        _print_router_debug(content, None, decision, None, "greeting")
        await _send_revealed(GREETING_REPLY)
        return

    if decision.intent == "company_eligibility":
        _print_router_debug(
            content,
            None,
            decision,
            "eligible_subjects",
            "BandoFacts + company_profile",
        )
        try:
            result = await cl.make_async(_run_company_eligibility_command)()
            await _send_revealed(normalize_visible_sources(result["markdown"]))
            await _send_sources(result["sources"])
        except Exception as exc:
            await _send_revealed(f"Errore nella verifica di ammissibilita': {exc}")
        return

    if decision.intent == "company_profile":
        _print_router_debug(content, None, decision, None, "company_profile")
        await dispatch_command("/azienda")
        return

    if decision.intent == "summary":
        _print_router_debug(content, None, decision, None, "BandoFacts")
        await dispatch_command("/summary")
        return

    if decision.intent == "participation_steps":
        _print_router_debug(
            content,
            None,
            decision,
            "participation_requirements",
            "BandoFacts",
        )
        status_msg = await _send_status(
            _thinking_content(
                "Percorso candidatura",
                "Recupero i passaggi operativi dai fatti estratti.",
            ),
            author="Candidatura",
        )
        animation = asyncio.create_task(
            _animate_status(
                status_msg,
                "Percorso candidatura",
                (
                    "Verifico soggetti ammessi e requisiti edificio...",
                    "Raccolgo documenti, scadenza e modalita'...",
                    "Compongo i passaggi essenziali...",
                ),
            )
        )
        await asyncio.sleep(0)
        try:
            result = await cl.make_async(_run_participation_steps_command)()
            await _stop_animation(animation)
            await _reveal_message(
                status_msg,
                normalize_visible_sources(result["markdown"]),
            )
            await _send_sources(result["sources"])
        except Exception as exc:
            await _stop_animation(animation)
            await _update_message(status_msg, f"Errore nel percorso candidatura: {exc}")
        return

    if decision.intent == "fact_qa" and decision.fact_topic != "none":
        _print_router_debug(
            content,
            None,
            decision,
            decision.fact_topic,
            "BandoFacts",
        )
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
            fact_result = await cl.make_async(_run_fact_qa_command)(decision.fact_topic)
            await _stop_animation(animation)
            if fact_result:
                _print_qa_debug(content, fact_result["topic"], "BandoFacts", False)
                await _reveal_message(
                    status_msg,
                    normalize_visible_sources(fact_result["markdown"]),
                )
                await _send_sources(fact_result["sources"])
                return
            _print_qa_debug(content, decision.fact_topic, "RAG", True)
            _print_router_debug(
                content,
                None,
                decision,
                decision.fact_topic,
                "RAG",
                True,
            )
            await _update_message(status_msg, "")
        except Exception:
            await _stop_animation(animation)
            _print_qa_debug(content, decision.fact_topic, "RAG", True)
            _print_router_debug(
                content,
                None,
                decision,
                decision.fact_topic,
                "RAG",
                True,
            )
            await _update_message(status_msg, "")
    else:
        if decision.intent == "help":
            _print_router_debug(content, None, decision, None, "help")
            await _send_revealed(HELP_REPLY)
            return
        _print_router_debug(content, None, decision, decision.fact_topic, "RAG", True)
        _print_qa_debug(content, None, "RAG", True, intent="document_qa")

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

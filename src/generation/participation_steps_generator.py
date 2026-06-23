from typing import Any

from src.extraction.bando_facts_extractor import (
    BandoFacts,
    extract_bando_facts,
)
from src.retrieval.rag_engine import RagEngine
from src.source_display import normalize_visible_sources


def _dedupe_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, int | None]] = set()
    for source in sources:
        clean = dict(source)
        clean["source"] = normalize_visible_sources(str(clean.get("source") or ""))
        key = (clean["source"], clean.get("page"))
        if not clean["source"] or key in seen:
            continue
        seen.add(key)
        deduped.append(clean)
    return sorted(
        deduped,
        key=lambda item: (
            item.get("page") is None,
            item.get("page") or 10**9,
            item.get("source", ""),
        ),
    )


def _compact_source_line(sources: list[dict[str, Any]]) -> str:
    deduped = _dedupe_sources(sources)
    if not deduped:
        return "Fonti: nessuna fonte recuperata."

    grouped: dict[str, list[int]] = {}
    fallback_sources: list[str] = []
    for source in deduped:
        source_text = str(source.get("source") or "")
        page = source.get("page")
        if ", pag." in source_text and page is not None:
            document_name = source_text.split(", pag.", 1)[0]
            grouped.setdefault(document_name, [])
            page_number = int(page)
            if page_number not in grouped[document_name]:
                grouped[document_name].append(page_number)
        elif source_text:
            fallback_sources.append(source_text)

    parts: list[str] = []
    for document_name, pages in grouped.items():
        page_text = "; ".join(f"pag. {page}" for page in sorted(pages))
        parts.append(f"{document_name}, {page_text}")
    parts.extend(fallback_sources)
    return f"Fonti: {'; '.join(parts)}"


def render_participation_steps(facts: BandoFacts) -> dict[str, Any]:
    sources: list[dict[str, Any]] = []
    for field in (
        facts.eligible_subjects,
        facts.building_requirements,
        facts.required_documents,
        facts.deadline,
        facts.submission_mode,
    ):
        sources.extend(field.sources[:1])
    clean_sources = _dedupe_sources(sources)
    source_line = _compact_source_line(clean_sources)

    markdown = f"""Per partecipare devi seguire questi passaggi principali:

1. Verificare che il soggetto proponente sia ammesso.

2. Verificare i requisiti dell'edificio.

3. Preparare la documentazione richiesta.

4. Presentare la domanda tramite PEC entro la scadenza indicata.

5. Verificare i dati mancanti dello scenario.

Per generare una checklist completa usa `/checklist`.

{source_line}"""

    return {
        "markdown": normalize_visible_sources(markdown),
        "sources": clean_sources,
    }


def generate_participation_steps(
    rag_engine: RagEngine | None = None,
) -> dict[str, Any]:
    facts = extract_bando_facts(rag_engine)
    return render_participation_steps(facts)

from pathlib import Path
from typing import Any

from src.extraction.bando_facts_extractor import (
    BandoFacts,
    INFO_NOT_RETRIEVED,
    extract_bando_facts,
)
from src.retrieval.rag_engine import RagEngine
from src.source_display import normalize_visible_sources


def _items(values: list[str]) -> str:
    if not values:
        return INFO_NOT_RETRIEVED
    return "\n".join(f"- {value}" for value in values)


def render_summary(facts: BandoFacts) -> str:
    sections = [
        ("Oggetto e finalita'", facts.object.value + facts.finality.value),
        ("Dotazione finanziaria", facts.financial_allocation.value),
        ("Soggetti ammessi", facts.eligible_subjects.value),
        ("Requisiti principali", facts.building_requirements.value),
        ("Presentazione della domanda", facts.deadline.value + facts.submission_mode.value),
        ("Documentazione richiesta", facts.required_documents.value),
        ("Valutazione", facts.evaluation_criteria.value),
        ("Obblighi successivi", facts.post_award_obligations.value),
        ("Informazioni da verificare", facts.missing_or_uncertain_fields.value),
    ]

    parts = ["# Riassunto operativo del bando"]
    for title, values in sections:
        parts.append(f"## {title}")
        parts.append(_items(values))
    return normalize_visible_sources("\n\n".join(parts).strip())


def generate_bando_summary(
    rag_engine: RagEngine | None = None,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    facts = extract_bando_facts(
        rag_engine,
        debug_label="SUMMARY DEBUG",
        intent="summary",
    )
    markdown = render_summary(facts)
    if output_path:
        Path(output_path).write_text(markdown, encoding="utf-8")

    return {
        "markdown": markdown,
        "sources": facts.sources,
        "facts": facts,
    }


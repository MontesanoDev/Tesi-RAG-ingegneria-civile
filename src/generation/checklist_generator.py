from pathlib import Path
from typing import Any

from src.extraction.bando_facts_extractor import (
    BandoFactField,
    BandoFacts,
    INFO_NOT_RETRIEVED,
    extract_bando_facts,
)
from src.generation.company_profile import DEFAULT_COMPANY_PROFILE, load_company_profile
from src.retrieval.rag_engine import RagEngine
from src.source_display import normalize_visible_sources


def _first_source(field: BandoFactField) -> str | None:
    if not field.sources:
        return None
    return str(field.sources[0].get("source") or "").strip() or None


def _source_line(field: BandoFactField, label: str = "Fonte") -> str:
    source = _first_source(field)
    if not source:
        return ""
    return f"\n  {label}: {source}"


def _field_has_value(field: BandoFactField) -> bool:
    return bool(field.value) and field.value != [INFO_NOT_RETRIEVED]


def _render_item(text: str, field: BandoFactField | None = None) -> str:
    source = _source_line(field) if field else ""
    return f"- [ ] {text}{source}"


def _render_field_items(field: BandoFactField) -> str:
    if not _field_has_value(field):
        return "- [ ] Informazione non recuperata nel contesto disponibile."
    return "\n".join(_render_item(value, field) for value in field.value)


def _render_document_items(facts: BandoFacts) -> str:
    field = facts.required_documents
    if not _field_has_value(field):
        return "- [ ] Informazione non recuperata nel contesto disponibile."

    source = _source_line(field, label="Fonti")
    lines = []
    for value in field.value:
        if "A1" in value or "Istanza" in value:
            lines.append("- [ ] Predisporre istanza di finanziamento.")
        elif "A2" in value or "Scheda tecnica" in value:
            lines.append("- [ ] Predisporre scheda tecnica della proposta progettuale.")
        elif "A3" in value or "Verifica climatica" in value:
            lines.append("- [ ] Predisporre verifica climatica.")
        elif "A4" in value or "DNSH" in value:
            lines.append("- [ ] Predisporre valutazione DNSH.")
        else:
            lines.append(f"- [ ] {value}")
    if source:
        lines.append(source.strip("\n"))
    return "\n".join(lines)


def _render_missing_items(facts: BandoFacts) -> str:
    return "\n".join(f"- [ ] {value}" for value in facts.missing_or_uncertain_fields.value)


def _join_sentences(values: list[str]) -> str:
    return " ".join(f"{value.rstrip('.')}." for value in values if value.strip())


def render_checklist(facts: BandoFacts) -> str:
    subject_text = (
        facts.eligible_subjects.value[0]
        if _field_has_value(facts.eligible_subjects)
        else INFO_NOT_RETRIEVED
    )
    building_items = _render_field_items(facts.building_requirements)
    deadline_text = (
        facts.deadline.value[0] if _field_has_value(facts.deadline) else INFO_NOT_RETRIEVED
    )
    submission_text = (
        facts.submission_mode.value[0]
        if _field_has_value(facts.submission_mode)
        else INFO_NOT_RETRIEVED
    )
    evaluation_text = (
        facts.evaluation_criteria.value[0]
        if _field_has_value(facts.evaluation_criteria)
        else INFO_NOT_RETRIEVED
    )
    post_award_text = (
        _join_sentences(facts.post_award_obligations.value)
        if _field_has_value(facts.post_award_obligations)
        else INFO_NOT_RETRIEVED
    )

    parts = [
        "# Checklist operativa per la candidatura",
        "## 1. Soggetti ammessi",
        _render_item(subject_text, facts.eligible_subjects)
        if _field_has_value(facts.eligible_subjects)
        else "- [ ] Informazione non recuperata nel contesto disponibile.",
        "## 2. Requisiti dell'edificio",
        building_items,
        "## 3. Termini",
        _render_item(deadline_text, facts.deadline)
        if _field_has_value(facts.deadline)
        else "- [ ] Informazione non recuperata nel contesto disponibile.",
        "## 4. Modalita' di presentazione",
        _render_item(submission_text, facts.submission_mode)
        if _field_has_value(facts.submission_mode)
        else "- [ ] Informazione non recuperata nel contesto disponibile.",
        "## 5. Documentazione da trasmettere",
        _render_document_items(facts),
        "## 6. Criteri di valutazione",
        _render_item(evaluation_text, facts.evaluation_criteria)
        if _field_has_value(facts.evaluation_criteria)
        else "- [ ] Informazione non recuperata nel contesto disponibile.",
        "## 7. Informazioni mancanti per lo scenario simulato",
        _render_missing_items(facts),
        "## 8. Obblighi successivi all'eventuale concessione",
        _render_item(post_award_text, facts.post_award_obligations)
        if _field_has_value(facts.post_award_obligations)
        else "- [ ] Informazione non recuperata nel contesto disponibile.",
    ]
    return normalize_visible_sources("\n\n".join(parts).strip())


def generate_checklist(
    rag_engine: RagEngine | None = None,
    company_profile_path: str | Path = DEFAULT_COMPANY_PROFILE,
) -> dict[str, Any]:
    company_profile = load_company_profile(company_profile_path)
    facts = extract_bando_facts(
        rag_engine,
        debug_label="CHECKLIST DEBUG",
        intent="checklist",
    )
    markdown = render_checklist(facts)

    return {
        "markdown": markdown,
        "sources": facts.sources,
        "company_profile_loaded": company_profile is not None,
        "facts": facts,
    }


def save_checklist(markdown: str, output_dir: str | Path = "outputs/checklist") -> Path:
    if not markdown or not markdown.strip():
        raise ValueError("Checklist vuota: niente da salvare.")

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    existing = sorted(directory.glob("checklist_*.md"))
    next_id = len(existing) + 1
    path = directory / f"checklist_{next_id:03d}.md"
    path.write_text(normalize_visible_sources(markdown), encoding="utf-8")
    return path

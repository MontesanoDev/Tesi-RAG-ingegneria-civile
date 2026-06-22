from typing import Any

from src.extraction.bando_facts_extractor import (
    BandoFactField,
    BandoFacts,
    INFO_NOT_RETRIEVED,
)
from src.routing.fact_topic_router import classify_fact_topic
from src.source_display import normalize_visible_sources


def _field_has_value(field: BandoFactField) -> bool:
    return bool(field.value) and field.value != [INFO_NOT_RETRIEVED]


def _dedupe_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in sources:
        source_text = normalize_visible_sources(str(source.get("source") or ""))
        if not source_text or source_text in seen:
            continue
        clean = dict(source)
        clean["source"] = source_text
        seen.add(source_text)
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
        return ""

    grouped: dict[str, list[int]] = {}
    fallback_sources: list[str] = []
    for source in deduped[:6]:
        source_text = str(source.get("source") or "")
        page = source.get("page")
        if ", pag." in source_text and page is not None:
            document_name = source_text.split(", pag.", 1)[0]
            grouped.setdefault(document_name, [])
            if int(page) not in grouped[document_name]:
                grouped[document_name].append(int(page))
        else:
            fallback_sources.append(source_text)

    parts: list[str] = []
    for document_name, pages in grouped.items():
        page_text = "; ".join(f"pag. {page}" for page in sorted(pages))
        parts.append(f"{document_name}, {page_text}")
    parts.extend(fallback_sources)
    return f"Fonte: {'; '.join(parts)}" if parts else ""


def _sentence(values: list[str]) -> str:
    return " ".join(f"{value.rstrip('.')}." for value in values if value.strip())


def _answer_for_topic(topic: str, facts: BandoFacts) -> tuple[str, list[dict[str, Any]]] | None:
    if topic == "eligible_subjects":
        if not _field_has_value(facts.eligible_subjects):
            return None
        values = list(facts.eligible_subjects.value)
        sources = list(facts.eligible_subjects.sources)
        if _field_has_value(facts.building_requirements):
            values.extend(facts.building_requirements.value[:2])
        subject_text = values[0].rstrip(".")
        if subject_text:
            subject_text = subject_text[0].lower() + subject_text[1:]
        requirement_text = _sentence(values[1:])
        answer = (
            "I soggetti ammessi sono "
            f"{subject_text}."
        )
        if requirement_text:
            answer = f"{answer} {requirement_text}"
        return answer, sources

    field = getattr(facts, topic, None)
    if not isinstance(field, BandoFactField) or not _field_has_value(field):
        return None

    value_text = _sentence(field.value)
    prefixes = {
        "title": "Il titolo identificativo estratto e': ",
        "object": "L'oggetto del bando riguarda: ",
        "finality": "La finalita' del bando e': ",
        "financial_allocation": "La dotazione finanziaria e gli importi principali sono: ",
        "building_requirements": "I requisiti principali dell'edificio sono: ",
        "deadline": "La scadenza estratta dal bando e': ",
        "submission_mode": "La modalita' di presentazione estratta dal bando e': ",
        "required_documents": "La documentazione da trasmettere comprende: ",
        "evaluation_criteria": "I criteri di valutazione estratti sono: ",
        "post_award_obligations": "Gli obblighi successivi all'eventuale concessione sono: ",
        "missing_or_uncertain_fields": "Le informazioni mancanti o da verificare sono: ",
    }
    return f"{prefixes.get(topic, '')}{value_text}", field.sources


def answer_document_question_from_facts(
    message: str,
    facts: BandoFacts,
) -> dict[str, Any] | None:
    topic = classify_fact_topic(message)
    if topic is None:
        return None

    topic_answer = _answer_for_topic(topic, facts)
    if topic_answer is None:
        return None

    answer, sources = topic_answer
    clean_sources = _dedupe_sources(sources)
    source_line = _compact_source_line(clean_sources)
    markdown = answer.strip()
    if source_line:
        markdown = f"{markdown}\n\n{source_line}"

    return {
        "topic": topic,
        "markdown": normalize_visible_sources(markdown),
        "sources": clean_sources,
    }

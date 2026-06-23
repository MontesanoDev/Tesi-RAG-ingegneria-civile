from typing import Any

from src.extraction.bando_facts_extractor import (
    BandoFactField,
    BandoFacts,
    INFO_NOT_RETRIEVED,
)
from src.generation.company_eligibility_generator import load_scenario_facts
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
    return f"Fonti: {'; '.join(parts)}" if parts else ""


def _sentence(values: list[str]) -> str:
    return " ".join(f"{value.rstrip('.')}." for value in values if value.strip())


def _inline_values(field: BandoFactField, fallback: str) -> str:
    if not _field_has_value(field):
        return fallback
    return "; ".join(value.rstrip(".") for value in field.value if value.strip())


def _source_for_page(sources: list[dict[str, Any]], page: int) -> dict[str, Any] | None:
    for source in sources:
        if source.get("page") == page:
            clean = dict(source)
            clean["source"] = normalize_visible_sources(str(clean.get("source") or ""))
            return clean
    return None


def _preferred_page_source(
    sources: list[dict[str, Any]],
    preferred_pages: tuple[int, ...],
) -> dict[str, Any] | None:
    for page in preferred_pages:
        source = _source_for_page(sources, page)
        if source:
            return source
    for source in sources:
        source_text = normalize_visible_sources(str(source.get("source") or ""))
        if source_text:
            clean = dict(source)
            clean["source"] = source_text
            return clean
    return None


def _sources_for_pages(
    sources: list[dict[str, Any]],
    preferred_pages: tuple[int, ...],
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen_pages: set[int] = set()
    for page in preferred_pages:
        source = _source_for_page(sources, page)
        if source and page not in seen_pages:
            selected.append(source)
            seen_pages.add(page)
    return selected


def _eligible_subjects_text(facts: BandoFacts) -> str:
    if not _field_has_value(facts.eligible_subjects):
        return "gli enti ammessi dal bando"

    text = facts.eligible_subjects.value[0].strip().rstrip(".")
    text = text.replace("Citta metropolitana", "Città metropolitana")
    if text.lower().startswith("enti locali pugliesi:"):
        details = text.split(":", 1)[1].strip()
        return f"enti locali pugliesi, cioè {details}"
    return text[:1].lower() + text[1:]


def _building_requirements_text(facts: BandoFacts) -> str:
    if not _field_has_value(facts.building_requirements):
        return "un edificio coerente con i requisiti del bando"

    values = [value.strip().rstrip(".") for value in facts.building_requirements.value[:2]]
    if not values:
        return "un edificio coerente con i requisiti del bando"

    first = values[0]
    if first.startswith("Edificio pubblico"):
        first = "un edificio pubblico" + first.removeprefix("Edificio pubblico")
    else:
        first = first[:1].lower() + first[1:]

    if len(values) == 1:
        return first

    second = values[1]
    if second.startswith("Edificio "):
        second = second.removeprefix("Edificio ")
    else:
        second = second[:1].lower() + second[1:]
    return f"{first}, {second}"


def _render_participation_requirements(facts: BandoFacts) -> tuple[str, list[dict[str, Any]]] | None:
    if not (
        _field_has_value(facts.eligible_subjects)
        or _field_has_value(facts.building_requirements)
    ):
        return None

    scenario = load_scenario_facts()
    company_short_name = (
        "MAPI" if scenario.company_name.lower().startswith("mapi") else scenario.company_name
    )
    answer = (
        "Il problema riguarda entrambi i livelli, ma in modo diverso:\n\n"
        f"1. Azienda/scenario: {scenario.company_name} non è soggetto proponente "
        f"diretto, perché il bando ammette {_eligible_subjects_text(facts)}. "
        f"{company_short_name} può però operare come {scenario.scenario_role}.\n\n"
        f"2. Edificio: l'intervento deve riguardare {_building_requirements_text(facts)}.\n\n"
        "Quindi per procedere servono sia un ente locale ammesso sia un edificio "
        "coerente con i requisiti del bando."
    )
    sources: list[dict[str, Any]] = []
    bando_source = _preferred_page_source(
        list(facts.eligible_subjects.sources) + list(facts.building_requirements.sources),
        (3,),
    )
    if bando_source:
        sources.append(bando_source)
    sources.extend(
        [
            {"source": "profilo MAPI", "page": None},
            {"source": "scenario demo", "page": None},
        ]
    )
    return answer, sources


def _render_submission_package(facts: BandoFacts) -> tuple[str, list[dict[str, Any]]] | None:
    if not (
        _field_has_value(facts.required_documents)
        and _field_has_value(facts.deadline)
        and _field_has_value(facts.submission_mode)
    ):
        return None

    document_lines: list[str] = []
    for index, value in enumerate(facts.required_documents.value):
        item = value.strip().rstrip(".")
        if item.startswith("Ulteriore "):
            item = "eventuale " + item[:1].lower() + item[1:]
        suffix = "." if index == len(facts.required_documents.value) - 1 else ";"
        document_lines.append(f"- {item}{suffix}")

    submission = facts.submission_mode.value[0].strip().rstrip(".")
    submission = submission.removeprefix("Presentazione ")
    if ", conservando " in submission:
        submission, receipt = submission.split(", conservando ", 1)
        receipt = f", conservando {receipt}"
    else:
        receipt = ""

    deadline = facts.deadline.value[0].strip().rstrip(".")
    deadline = deadline.removeprefix("Presentazione ")

    answer = (
        "Devi predisporre e trasmettere la documentazione principale prevista dal bando:\n\n"
        f"{chr(10).join(document_lines)}\n\n"
        f"La domanda deve essere presentata {submission} {deadline}{receipt}."
    )

    sources = []
    sources.extend(_sources_for_pages(facts.required_documents.sources, (4, 24)))
    sources.extend(_sources_for_pages(facts.submission_mode.sources, (23,)))
    return answer, sources


def _answer_for_topic(topic: str, facts: BandoFacts) -> tuple[str, list[dict[str, Any]]] | None:
    if topic == "participation_requirements":
        return _render_participation_requirements(facts)

    if topic == "submission_package":
        return _render_submission_package(facts)

    if topic == "missing_information":
        topic = "missing_or_uncertain_fields"

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


def answer_fact_topic(
    topic: str,
    facts: BandoFacts,
) -> dict[str, Any] | None:
    if not topic or topic == "none":
        return None

    topic_answer = _answer_for_topic(topic, facts)
    if topic_answer is None:
        return None

    answer, sources = topic_answer
    clean_sources = _dedupe_sources(sources)
    source_line = _compact_source_line(clean_sources)
    if topic in {"participation_requirements", "submission_package"} and source_line:
        source_line = source_line.rstrip(".") + "."
    markdown = answer.strip()
    if source_line:
        markdown = f"{markdown}\n\n{source_line}"

    return {
        "topic": topic,
        "markdown": normalize_visible_sources(markdown),
        "sources": clean_sources,
    }


def answer_document_question_from_facts(
    message: str,
    facts: BandoFacts,
    topic: str | None = None,
) -> dict[str, Any] | None:
    if topic is None:
        from src.routing.semantic_router import classify_message

        decision = classify_message(message)
        if decision.intent != "fact_qa":
            return None
        topic = decision.fact_topic
    return answer_fact_topic(topic, facts)

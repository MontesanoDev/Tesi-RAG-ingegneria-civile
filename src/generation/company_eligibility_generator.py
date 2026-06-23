import re
from typing import Any

from pydantic import BaseModel, Field

from src.extraction.bando_facts_extractor import (
    BandoFactField,
    BandoFacts,
    INFO_NOT_RETRIEVED,
    extract_bando_facts,
)
from src.generation.company_profile import (
    DEFAULT_COMPANY_PROFILE,
    load_company_profile,
)
from src.retrieval.rag_engine import RagEngine
from src.source_display import normalize_visible_sources


class ScenarioFacts(BaseModel):
    company_name: str
    direct_applicant: bool
    scenario_role: str
    eligibility_basis: str
    notes: list[str] = Field(default_factory=list)


DEFAULT_SCENARIO_FACTS = ScenarioFacts(
    company_name="MAPI Ingegneria S.r.l.",
    direct_applicant=False,
    scenario_role="supporto tecnico a un ente locale nella preparazione della candidatura",
    eligibility_basis="eligible_subjects",
    notes=[
        "MAPI è una società di ingegneria simulata nello scenario dimostrativo.",
        "Il soggetto proponente del bando è un ente locale ammesso dall'avviso.",
    ],
)


def _field_has_value(field: BandoFactField) -> bool:
    return bool(field.value) and field.value != [INFO_NOT_RETRIEVED]


def _company_name_from_profile(profile: str | None) -> str | None:
    if not profile:
        return None
    match = re.search(r"^\s*nome:\s*(?P<name>.+?)\s*$", profile, re.MULTILINE)
    if not match:
        return None
    return match.group("name").strip().strip("\"'")


def load_scenario_facts(
    company_profile_path=DEFAULT_COMPANY_PROFILE,
) -> ScenarioFacts:
    profile = load_company_profile(company_profile_path)
    company_name = _company_name_from_profile(profile) or DEFAULT_SCENARIO_FACTS.company_name
    return DEFAULT_SCENARIO_FACTS.model_copy(update={"company_name": company_name})


def _eligible_subjects_text(facts: BandoFacts) -> str:
    if not _field_has_value(facts.eligible_subjects):
        return "i soggetti indicati dal bando come ammissibili"

    text = facts.eligible_subjects.value[0].strip().rstrip(".")
    text = text.replace("Citta metropolitana", "Città metropolitana")
    if text.lower().startswith("enti locali pugliesi:"):
        details = text.split(":", 1)[1].strip()
        return f"enti locali pugliesi, cioè {details}"
    return text[:1].lower() + text[1:]


def _preferred_eligible_source(facts: BandoFacts) -> dict[str, Any] | None:
    sources: list[dict[str, Any]] = []
    for source in facts.eligible_subjects.sources:
        source_text = normalize_visible_sources(str(source.get("source") or ""))
        if not source_text:
            continue
        clean = dict(source)
        clean["source"] = source_text
        sources.append(clean)

    if not sources:
        return None

    return sorted(
        sources,
        key=lambda source: (
            source.get("page") != 3,
            source.get("page") is None,
            source.get("page") or 10**9,
        ),
    )[0]


def render_company_eligibility(
    facts: BandoFacts,
    company_profile_path=DEFAULT_COMPANY_PROFILE,
    scenario_facts: ScenarioFacts | None = None,
) -> dict[str, Any]:
    profile = load_company_profile(company_profile_path)
    scenario = scenario_facts or load_scenario_facts(company_profile_path)
    bando_source = _preferred_eligible_source(facts)

    source_parts: list[str] = []
    sources: list[dict[str, Any]] = []
    if bando_source:
        source_parts.append(str(bando_source["source"]))
        sources.append(bando_source)
    if profile:
        source_parts.append("profilo MAPI")
        sources.append({"source": "profilo MAPI", "page": None})
    source_parts.append("scenario demo")
    sources.append({"source": "scenario demo", "page": None})

    source_line = (
        f"Fonti: {'; '.join(source_parts)}."
        if source_parts
        else "Fonti: scenario demo."
    )

    company_short_name = (
        "MAPI" if scenario.company_name.lower().startswith("mapi") else scenario.company_name
    )
    direct_answer = (
        f"Sì, nello scenario considerato {scenario.company_name} può presentare "
        "direttamente domanda come soggetto proponente."
        if scenario.direct_applicant
        else f"No, nello scenario considerato {scenario.company_name} non può "
        "presentare direttamente domanda come soggetto proponente."
    )

    markdown = (
        f"{direct_answer}\n\n"
        f"Il bando ammette {_eligible_subjects_text(facts)}.\n\n"
        f"{company_short_name} può invece operare come {scenario.scenario_role}.\n\n"
        f"{source_line}"
    )

    return {
        "topic": "eligible_subjects",
        "markdown": normalize_visible_sources(markdown),
        "sources": sources,
        "source": "BandoFacts + company_profile + ScenarioFacts",
        "fallback_to_rag": False,
    }


def generate_company_eligibility(
    rag_engine: RagEngine | None = None,
) -> dict[str, Any]:
    facts = extract_bando_facts(rag_engine)
    return render_company_eligibility(facts)

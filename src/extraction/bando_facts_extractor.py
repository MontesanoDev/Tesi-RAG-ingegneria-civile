from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
from string import punctuation
from typing import Any
import unicodedata

from src.indexing.index_builder import (
    DEFAULT_COLLECTION,
    DEFAULT_INDEX_DIR,
    DEFAULT_MANIFEST,
)
from src.retrieval.rag_engine import RagEngine
from src.source_display import normalize_visible_sources


FACTS_SCHEMA_VERSION = 3
FACTS_CACHE_PATH = Path("outputs/cache/bando_facts.json")
FIELD_TOP_K = 8
MIN_RELEVANT_CHUNKS = 3
INFO_NOT_RETRIEVED = "Informazione non recuperata nel contesto disponibile."
VERIFY_FULL_DOCUMENT = "Da verificare nel documento completo."

MISSING_OR_UNCERTAIN_FIELDS = [
    "Codice edificio / SNAES.",
    "Quadro economico.",
    "Livello progettuale disponibile.",
    "Dati tecnici dell'edificio.",
    "Documenti tecnici gia' disponibili.",
]


@dataclass(frozen=True)
class FieldSpec:
    name: str
    queries: tuple[str, ...]
    fallback_queries: tuple[str, ...]
    evidence_terms: tuple[str, ...]


@dataclass
class BandoFactField:
    value: list[str] = field(default_factory=list)
    sources: list[dict[str, Any]] = field(default_factory=list)
    queries: list[str] = field(default_factory=list)
    chunks: int = 0
    pages: list[int] = field(default_factory=list)
    section_titles: list[str] = field(default_factory=list)
    fallback_used: bool = False

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BandoFactField":
        return cls(
            value=list(payload.get("value") or []),
            sources=list(payload.get("sources") or []),
            queries=list(payload.get("queries") or []),
            chunks=int(payload.get("chunks") or 0),
            pages=list(payload.get("pages") or []),
            section_titles=list(payload.get("section_titles") or []),
            fallback_used=bool(payload.get("fallback_used")),
        )


FACT_FIELD_ORDER = [
    "title",
    "object",
    "finality",
    "financial_allocation",
    "eligible_subjects",
    "building_requirements",
    "deadline",
    "submission_mode",
    "required_documents",
    "evaluation_criteria",
    "post_award_obligations",
    "missing_or_uncertain_fields",
]


@dataclass
class BandoFacts:
    title: BandoFactField
    object: BandoFactField
    finality: BandoFactField
    financial_allocation: BandoFactField
    eligible_subjects: BandoFactField
    building_requirements: BandoFactField
    deadline: BandoFactField
    submission_mode: BandoFactField
    required_documents: BandoFactField
    evaluation_criteria: BandoFactField
    post_award_obligations: BandoFactField
    missing_or_uncertain_fields: BandoFactField
    sources: list[dict[str, Any]] = field(default_factory=list)
    cache_key: str | None = None

    def iter_fields(self):
        for name in FACT_FIELD_ORDER:
            yield name, getattr(self, name)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BandoFacts":
        field_payloads = {
            name: BandoFactField.from_dict(payload.get(name) or {})
            for name in FACT_FIELD_ORDER
        }
        return cls(
            **field_payloads,
            sources=list(payload.get("sources") or []),
            cache_key=payload.get("cache_key"),
        )


FIELD_SPECS: dict[str, FieldSpec] = {
    "title": FieldSpec(
        name="title",
        queries=(
            "Avviso pubblico selezione proposte progettuali infrastrutture istruzione primaria secondaria infanzia finalita",
            "finalita ambito applicazione infrastrutture istruzione formazione",
        ),
        fallback_queries=(
            "avviso pubblico edilizia scolastica Regione Puglia",
            "selezione proposte progettuali istruzione infanzia",
        ),
        evidence_terms=(
            "avviso pubblico",
            "edilizia scolastica",
            "istruzione primaria",
            "istruzione secondaria",
            "infanzia",
            "regione puglia",
        ),
    ),
    "object": FieldSpec(
        name="object",
        queries=(
            "Avviso pubblico selezione proposte progettuali infrastrutture istruzione primaria secondaria infanzia finalita",
            "finalita ambito applicazione infrastrutture istruzione formazione",
        ),
        fallback_queries=(
            "oggetto interventi infrastrutture scolastiche",
            "proposte progettuali istruzione primaria secondaria infanzia",
        ),
        evidence_terms=(
            "oggetto",
            "proposte progettuali",
            "infrastrutture",
            "istruzione primaria",
            "istruzione secondaria",
            "infanzia",
        ),
    ),
    "finality": FieldSpec(
        name="finality",
        queries=(
            "Avviso pubblico selezione proposte progettuali infrastrutture istruzione primaria secondaria infanzia finalita",
            "finalita ambito applicazione infrastrutture istruzione formazione",
        ),
        fallback_queries=(
            "finalita avviso edilizia scolastica",
            "obiettivo bando infrastrutture istruzione formazione",
        ),
        evidence_terms=(
            "finalita",
            "obiettivo",
            "istruzione",
            "formazione",
            "infrastrutture",
        ),
    ),
    "financial_allocation": FieldSpec(
        name="financial_allocation",
        queries=(
            "dotazione finanziaria 56.000.000 euro",
            "stanziato risorse pari a 56.000.000",
            "costo totale proposta progettuale non inferiore 500.000",
        ),
        fallback_queries=(
            "dotazione finanziaria",
            "risorse disponibili euro",
            "costo totale proposta progettuale",
        ),
        evidence_terms=(
            "dotazione finanziaria",
            "56 000 000",
            "stanziato",
            "risorse",
            "500 000",
            "costo totale",
        ),
    ),
    "eligible_subjects": FieldSpec(
        name="eligible_subjects",
        queries=(
            "soggetti proponenti Comuni Citta metropolitana di Bari Province pugliesi",
            "proprietari edifici pubblici scolastici SNAES validato",
            "Anagrafe Regionale Edilizia Scolastica Repertorio Fabbisogno regionale",
        ),
        fallback_queries=(
            "soggetti proponenti",
            "Comuni Province Citta metropolitana",
            "proprietari edifici pubblici scolastici",
            "requisiti di ammissibilita",
        ),
        evidence_terms=(
            "soggetti proponenti",
            "comuni",
            "province",
            "citta metropolitana",
            "proprietari",
            "edifici pubblici",
            "snaes",
            "anagrafe regionale edilizia scolastica",
        ),
    ),
    "building_requirements": FieldSpec(
        name="building_requirements",
        queries=(
            "edificio pubblico scolastico Anagrafe Regionale Edilizia Scolastica SNAES validato Repertorio Fabbisogno regionale edilizia scolastica",
            "edifici pubblici adibiti a scuole istruzione primaria secondaria infanzia",
            "Repertorio del Fabbisogno regionale di edilizia scolastica",
        ),
        fallback_queries=(
            "edifici pubblici scolastici",
            "SNAES validato",
            "Anagrafe Regionale Edilizia Scolastica",
            "Repertorio Fabbisogno edilizia scolastica",
        ),
        evidence_terms=(
            "edificio",
            "edifici pubblici",
            "scuola",
            "scuole",
            "infanzia",
            "anagrafe regionale",
            "edilizia scolastica",
            "snaes",
            "repertorio",
            "fabbisogno",
        ),
    ),
    "deadline": FieldSpec(
        name="deadline",
        queries=(
            "termine scadenza presentazione istanze ore 12.00 15.09.2025",
            "presentazione istanze partecipazione ore 12.00 15 settembre 2025",
            "6.1 Termini",
        ),
        fallback_queries=(
            "15 settembre 2025 ore 12",
            "15.09.2025 ore 12.00",
            "scadenza istanza",
            "termini presentazione istanze",
        ),
        evidence_terms=(
            "termine",
            "scadenza",
            "presentazione istanze",
            "ore 12",
            "12 00",
            "15 09 2025",
            "15 settembre 2025",
        ),
    ),
    "submission_mode": FieldSpec(
        name="submission_mode",
        queries=(
            "modalita presentazione istanza PEC ricevuta consegna",
            "6.2 Modalita di presentazione dell'istanza",
            "servizio.lavoripubblici@pec.rupar.puglia.it",
        ),
        fallback_queries=(
            "presentazione istanza PEC",
            "ricevuta consegna",
            "servizio lavori pubblici pec rupar puglia",
            "modalita presentazione istanza",
        ),
        evidence_terms=(
            "modalita",
            "presentazione istanza",
            "pec",
            "ricevuta",
            "consegna",
            "servizio lavoripubblici pec rupar puglia",
        ),
    ),
    "required_documents": FieldSpec(
        name="required_documents",
        queries=(
            "documentazione da trasmettere A1 Istanza A2 scheda tecnica A3 verifica climatica A4 DNSH",
            "6.3 Documentazione da trasmettere",
            "Allegato A1 A2 A3 A4 B disciplinare",
        ),
        fallback_queries=(
            "A1 A2 A3 A4 DNSH",
            "scheda tecnica verifica climatica",
            "istanza finanziamento documentazione",
            "allegati da trasmettere",
        ),
        evidence_terms=(
            "documentazione",
            "allegato",
            "a1",
            "a2",
            "a3",
            "a4",
            "istanza",
            "scheda tecnica",
            "verifica climatica",
            "dnsh",
        ),
    ),
    "evaluation_criteria": FieldSpec(
        name="evaluation_criteria",
        queries=(
            "criteri valutazione punteggio massimo 90 soglia minima 54",
            "valutazione tecnica criteri A B C D E F",
            "attribuzione punteggio griglia valutazione",
        ),
        fallback_queries=(
            "punteggio massimo 90",
            "soglia minima 54",
            "criteri valutazione tecnica",
            "griglia di valutazione",
        ),
        evidence_terms=(
            "criteri",
            "valutazione",
            "punteggio",
            "90",
            "54",
            "soglia",
            "griglia",
        ),
    ),
    "post_award_obligations": FieldSpec(
        name="post_award_obligations",
        queries=(
            "obblighi beneficiario avvio gara CIG entro un anno",
            "monitoraggio rendicontazione revoca concessione contributo",
            "obblighi successivi concessione contributo",
        ),
        fallback_queries=(
            "obblighi beneficiario",
            "rendicontazione monitoraggio revoca",
            "avvio gara CIG",
            "concessione contributo obblighi",
        ),
        evidence_terms=(
            "obblighi",
            "beneficiario",
            "avvio gara",
            "cig",
            "monitoraggio",
            "rendicontazione",
            "revoca",
            "concessione contributo",
        ),
    ),
}

SOURCE_PRIORITY_TERMS: dict[str, tuple[str, ...]] = {
    "title": ("avviso pubblico", "regione puglia", "edilizia scolastica"),
    "object": ("oggetto", "proposte progettuali", "infrastrutture"),
    "finality": ("finalita", "obiettivo", "infrastrutture"),
    "financial_allocation": ("56 000 000", "56.000.000", "500 000", "500.000"),
    "eligible_subjects": (
        "soggetti proponenti",
        "comuni",
        "province",
        "citta metropolitana",
        "proprietari",
    ),
    "building_requirements": (
        "snaes",
        "anagrafe regionale",
        "edifici pubblici",
        "repertorio",
        "fabbisogno",
    ),
    "deadline": (
        "6 1",
        "termini",
        "15 09 2025",
        "15 settembre 2025",
        "ore 12",
        "12 00",
    ),
    "submission_mode": (
        "6 2",
        "modalita",
        "pec",
        "servizio lavoripubblici pec rupar puglia it",
        "ricevuta consegna",
    ),
    "required_documents": (
        "6 3",
        "documentazione da trasmettere",
        "a1",
        "a2",
        "a3",
        "a4",
        "dnsh",
    ),
    "evaluation_criteria": (
        "valutazione tecnica",
        "criteri",
        "punteggio massimo 90",
        "soglia minima 54",
        "griglia",
    ),
    "post_award_obligations": (
        "obblighi",
        "avvio gara",
        "cig",
        "monitoraggio",
        "rendicontazione",
        "revoca",
    ),
}


def _normalize_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    without_punctuation = without_accents.translate(
        str.maketrans({char: " " for char in punctuation})
    )
    return " ".join(without_punctuation.lower().split())


def _contains_any(text: str, terms: tuple[str, ...] | list[str]) -> bool:
    normalized = _normalize_text(text)
    return any(_normalize_text(term) in normalized for term in terms)


def _contains_groups(text: str, groups: list[list[str]]) -> bool:
    normalized = _normalize_text(text)
    return all(
        any(_normalize_text(term) in normalized for term in group)
        for group in groups
    )


def _clean_source(source: dict[str, Any]) -> dict[str, Any]:
    clean = dict(source)
    clean["source"] = normalize_visible_sources(
        str(clean.get("source") or "Fonte sconosciuta")
    )
    page = clean.get("page")
    try:
        clean["page"] = int(page) if page is not None else None
    except (TypeError, ValueError):
        clean["page"] = None
    return clean


def _source_key(source: dict[str, Any]) -> tuple[str, int | None]:
    return (str(source.get("source") or ""), source.get("page"))


def _dedupe_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, int | None]] = set()
    for source in sources:
        clean = _clean_source(source)
        key = _source_key(clean)
        if key in seen:
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


def _dedupe_sources_in_order(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, int | None]] = set()
    for source in sources:
        clean = _clean_source(source)
        key = _source_key(clean)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(clean)
    return deduped


def _context(records: list[dict[str, Any]]) -> str:
    return "\n\n".join(str(record.get("text") or "") for record in records)


def _records_matching(
    records: list[dict[str, Any]],
    terms: tuple[str, ...] | list[str],
) -> list[dict[str, Any]]:
    return [record for record in records if _contains_any(record.get("text", ""), terms)]


def _sources_from_records(
    records: list[dict[str, Any]],
    limit: int = 4,
) -> list[dict[str, Any]]:
    return _dedupe_sources_in_order(
        [record["source"] for record in records if record.get("source")]
    )[:limit]


def _record_priority_score(record: dict[str, Any], terms: tuple[str, ...]) -> int:
    haystack = " ".join(
        [
            str(record.get("text") or ""),
            str(record.get("source", {}).get("section") or ""),
            str(record.get("source", {}).get("section_title") or ""),
        ]
    )
    normalized = _normalize_text(haystack)
    return sum(1 for term in terms if _normalize_text(term) in normalized)


def _rank_source_records(
    field_name: str,
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    terms = SOURCE_PRIORITY_TERMS.get(field_name, ())
    return sorted(
        records,
        key=lambda record: (
            -_record_priority_score(record, terms),
            record.get("source", {}).get("page") is None,
            record.get("source", {}).get("page") or 10**9,
        ),
    )


def _pages_from_records(records: list[dict[str, Any]]) -> list[int]:
    pages = {
        record.get("source", {}).get("page")
        for record in records
        if record.get("source", {}).get("page") is not None
    }
    return sorted(int(page) for page in pages)


def _section_titles_from_records(records: list[dict[str, Any]]) -> list[str]:
    titles = {
        str(record.get("source", {}).get("section_title"))
        for record in records
        if record.get("source", {}).get("section_title")
    }
    return sorted(titles)


def _retrieve_query(engine: RagEngine, query: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    vector_result = engine.retrieve(
        query,
        similarity_top_k=FIELD_TOP_K,
        dedupe_sources=False,
    )
    keyword_result = (
        engine.keyword_search(query, top_k=FIELD_TOP_K)
        if hasattr(engine, "keyword_search")
        else {"texts": [], "sources": []}
    )

    for result in (vector_result, keyword_result):
        for text, source in zip(result.get("texts") or [], result.get("sources") or []):
            records.append(
                {
                    "text": normalize_visible_sources(str(text or "")),
                    "source": _clean_source(source),
                    "query": query,
                }
            )
    return records


def _relevant_records(
    records: list[dict[str, Any]],
    spec: FieldSpec,
) -> list[dict[str, Any]]:
    relevant: list[dict[str, Any]] = []
    for record in records:
        haystack = " ".join(
            [
                str(record.get("text") or ""),
                str(record.get("source", {}).get("section") or ""),
                str(record.get("source", {}).get("section_title") or ""),
            ]
        )
        if _contains_any(haystack, spec.evidence_terms):
            relevant.append(record)
    return relevant


def _retrieve_field(engine: RagEngine, spec: FieldSpec) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    queries_used = list(spec.queries)
    fallback_used = False

    for query in spec.queries:
        records.extend(_retrieve_query(engine, query))

    relevant = _relevant_records(records, spec)
    if len(relevant) < MIN_RELEVANT_CHUNKS:
        fallback_used = True
        queries_used.extend(spec.fallback_queries)
        for query in spec.fallback_queries:
            records.extend(_retrieve_query(engine, query))
        relevant = _relevant_records(records, spec)

    return {
        "records": records,
        "relevant_records": relevant,
        "queries_used": queries_used,
        "fallback_used": fallback_used,
    }


def _value_title(records: list[dict[str, Any]]) -> list[str]:
    if not records:
        return [INFO_NOT_RETRIEVED]
    return ["Avviso Edilizia Scolastica Puglia 2025."]


def _value_object(records: list[dict[str, Any]]) -> list[str]:
    if not records:
        return [INFO_NOT_RETRIEVED]
    context = _context(records)
    if _contains_any(context, ("proposte progettuali", "infrastrutture", "istruzione")):
        return [
            "Selezione di proposte progettuali relative a infrastrutture per "
            "istruzione primaria, secondaria e infanzia."
        ]
    return [VERIFY_FULL_DOCUMENT]


def _value_finality(records: list[dict[str, Any]]) -> list[str]:
    if not records:
        return [INFO_NOT_RETRIEVED]
    context = _context(records)
    if _contains_any(context, ("finalita", "obiettivo", "istruzione", "formazione")):
        return [
            "Sostenere interventi su infrastrutture scolastiche e formative nel "
            "territorio regionale."
        ]
    return [VERIFY_FULL_DOCUMENT]


def _value_financial_allocation(records: list[dict[str, Any]]) -> list[str]:
    if not records:
        return [INFO_NOT_RETRIEVED]
    context = _context(records)
    values: list[str] = []
    if _contains_any(context, ("56 000 000", "56.000.000")):
        values.append("Dotazione finanziaria pari a 56.000.000 euro.")
    if _contains_any(context, ("500 000", "500.000")):
        values.append(
            "Costo totale della proposta progettuale non inferiore a 500.000 euro."
        )
    return values or [VERIFY_FULL_DOCUMENT]


def _value_eligible_subjects(records: list[dict[str, Any]]) -> list[str]:
    if not records:
        return [INFO_NOT_RETRIEVED]
    context = _context(records)
    if _contains_groups(
        context,
        [
            ["comuni", "comune"],
            ["province", "provincia"],
            ["citta metropolitana"],
        ],
    ):
        return [
            "Enti locali pugliesi: Comuni, Citta metropolitana di Bari o "
            "Province proprietari di edifici pubblici scolastici."
        ]
    if _contains_any(context, ("soggetti proponenti", "enti locali", "proprietari")):
        return ["Soggetti proponenti da verificare nel documento completo."]
    return [VERIFY_FULL_DOCUMENT]


def _value_building_requirements(records: list[dict[str, Any]]) -> list[str]:
    if not records:
        return [INFO_NOT_RETRIEVED]
    context = _context(records)
    values: list[str] = []
    if _contains_any(context, ("edifici pubblici", "edificio pubblico", "scuole", "infanzia")):
        values.append("Edificio pubblico adibito a scuola o struttura educativa.")
    if _contains_any(context, ("anagrafe regionale", "snaes")):
        values.append(
            "Edificio censito nell'Anagrafe Regionale di Edilizia Scolastica "
            "con SNAES validato."
        )
    if _contains_any(context, ("repertorio", "fabbisogno")):
        values.append(
            "Coerenza con il Repertorio del Fabbisogno regionale di edilizia "
            "scolastica, se richiesto dall'avviso."
        )
    return values or [VERIFY_FULL_DOCUMENT]


def _value_deadline(records: list[dict[str, Any]]) -> list[str]:
    if not records:
        return [INFO_NOT_RETRIEVED]
    context = _context(records)
    has_date = _contains_any(context, ("15 09 2025", "15 settembre 2025", "15/09/2025"))
    has_time = _contains_any(context, ("ore 12", "12 00", "12:00"))
    if has_date and has_time:
        return ["Presentazione entro le ore 12:00 del 15/09/2025."]
    if has_date:
        return ["Scadenza indicata al 15/09/2025; orario da verificare."]
    return [VERIFY_FULL_DOCUMENT]


def _value_submission_mode(records: list[dict[str, Any]]) -> list[str]:
    if not records:
        return [INFO_NOT_RETRIEVED]
    context = _context(records)
    has_email = _contains_any(
        context,
        (
            "servizio lavoripubblici pec rupar puglia it",
            "servizio.lavoripubblici@pec.rupar.puglia.it",
        ),
    )
    if has_email:
        return [
            "Presentazione tramite PEC all'indirizzo "
            "servizio.lavoripubblici@pec.rupar.puglia.it, conservando la ricevuta "
            "di consegna."
        ]
    if _contains_any(context, ("pec", "ricevuta", "consegna")):
        return ["Presentazione tramite PEC secondo le modalita previste dall'avviso."]
    return [VERIFY_FULL_DOCUMENT]


def _value_required_documents(records: list[dict[str, Any]]) -> list[str]:
    if not records:
        return [INFO_NOT_RETRIEVED]
    context = _context(records)
    values: list[str] = []
    if _contains_any(context, ("a1", "istanza di finanziamento", "istanza")):
        values.append("Istanza di finanziamento (Allegato A1).")
    if _contains_any(context, ("a2", "scheda tecnica")):
        values.append("Scheda tecnica della proposta progettuale (Allegato A2).")
    if _contains_any(context, ("a3", "verifica climatica")):
        values.append("Verifica climatica (Allegato A3).")
    if _contains_any(context, ("a4", "dnsh")):
        values.append("Valutazione DNSH (Allegato A4).")
    if _contains_any(context, ("allegato b", "disciplinare")):
        values.append("Ulteriore documentazione/disciplinare indicato dall'avviso.")
    return values or [VERIFY_FULL_DOCUMENT]


def _value_evaluation_criteria(records: list[dict[str, Any]]) -> list[str]:
    if not records:
        return [INFO_NOT_RETRIEVED]
    context = _context(records)
    has_90 = _contains_any(context, ("punteggio massimo 90", "massimo 90", "90"))
    has_54 = _contains_any(context, ("soglia minima 54", "minima 54", "54"))
    if has_90 and has_54:
        return [
            "Valutazione tecnica con criteri A-F, punteggio massimo 90 e "
            "soglia minima 54."
        ]
    if _contains_any(context, ("criteri", "valutazione", "punteggio", "griglia")):
        return ["Criteri e punteggi di valutazione da verificare nel documento completo."]
    return [VERIFY_FULL_DOCUMENT]


def _value_post_award_obligations(records: list[dict[str, Any]]) -> list[str]:
    if not records:
        return [INFO_NOT_RETRIEVED]
    context = _context(records)
    values: list[str] = []
    if _contains_any(context, ("avvio gara", "cig", "entro un anno")):
        values.append("Avvio della gara/CIG secondo i termini indicati dall'avviso.")
    if _contains_any(context, ("monitoraggio", "rendicontazione", "revoca")):
        values.append("Monitoraggio, rendicontazione e possibili revoche del contributo.")
    if not values and _contains_any(context, ("obblighi", "beneficiario")):
        values.append("Obblighi del beneficiario successivi all'eventuale concessione.")
    return values or [VERIFY_FULL_DOCUMENT]


VALUE_BUILDERS = {
    "title": _value_title,
    "object": _value_object,
    "finality": _value_finality,
    "financial_allocation": _value_financial_allocation,
    "eligible_subjects": _value_eligible_subjects,
    "building_requirements": _value_building_requirements,
    "deadline": _value_deadline,
    "submission_mode": _value_submission_mode,
    "required_documents": _value_required_documents,
    "evaluation_criteria": _value_evaluation_criteria,
    "post_award_obligations": _value_post_award_obligations,
}


def _build_field(spec: FieldSpec, retrieval: dict[str, Any]) -> BandoFactField:
    relevant = retrieval["relevant_records"]
    builder = VALUE_BUILDERS[spec.name]
    values = [normalize_visible_sources(value) for value in builder(relevant)]
    source_records = (
        _records_matching(relevant, spec.evidence_terms)
        or relevant
        or retrieval["records"]
    )
    source_records = _rank_source_records(spec.name, source_records)
    sources = [] if values == [INFO_NOT_RETRIEVED] else _sources_from_records(source_records)
    return BandoFactField(
        value=values,
        sources=sources,
        queries=list(retrieval["queries_used"]),
        chunks=len(relevant),
        pages=_pages_from_records(relevant),
        section_titles=_section_titles_from_records(relevant),
        fallback_used=bool(retrieval["fallback_used"]),
    )


def _missing_field() -> BandoFactField:
    return BandoFactField(value=list(MISSING_OR_UNCERTAIN_FIELDS))


def _manifest_for_cache(index_dir: str | Path) -> dict[str, Any] | None:
    path = Path(index_dir) / DEFAULT_MANIFEST
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _cache_key(index_dir: str | Path, collection_name: str) -> str | None:
    manifest = _manifest_for_cache(index_dir)
    if not manifest:
        return None
    payload = {
        "facts_schema_version": FACTS_SCHEMA_VERSION,
        "index_schema_version": manifest.get("schema_version"),
        "collection": collection_name,
        "index_collection": manifest.get("collection"),
        "fingerprint": manifest.get("fingerprint"),
        "chunks": manifest.get("chunks"),
        "document_pages": manifest.get("document_pages"),
        "pdfs": manifest.get("pdfs"),
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_cached_facts(cache_key: str | None) -> BandoFacts | None:
    if not cache_key or not FACTS_CACHE_PATH.exists():
        return None
    try:
        payload = json.loads(FACTS_CACHE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if payload.get("cache_key") != cache_key:
        return None
    return BandoFacts.from_dict(payload)


def _write_cached_facts(facts: BandoFacts) -> None:
    if not facts.cache_key:
        return
    FACTS_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FACTS_CACHE_PATH.write_text(
        json.dumps(facts.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _print_debug(
    facts: BandoFacts,
    debug_label: str,
    intent: str | None = None,
) -> None:
    for field_name, fact_field in facts.iter_fields():
        if field_name == "missing_or_uncertain_fields":
            continue
        print(f"[{debug_label}]")
        if intent:
            print(f"intent: {intent}")
        print("using: extract_bando_facts()")
        print(f"field: {field_name}")
        print(f"queries: {fact_field.queries}")
        print(f"chunks: {fact_field.chunks}")
        print(f"pages: {fact_field.pages}")
        print(f"section_titles: {fact_field.section_titles}")
        print(f"fallback: {'yes' if fact_field.fallback_used else 'no'}")


def extract_bando_facts(
    rag_engine: RagEngine | None = None,
    *,
    use_cache: bool = True,
    debug_label: str | None = None,
    intent: str | None = None,
) -> BandoFacts:
    engine = rag_engine or RagEngine(
        collection_name=DEFAULT_COLLECTION,
        similarity_top_k=FIELD_TOP_K,
        streaming=False,
        build_query_engine=False,
    )
    cache_key = _cache_key(engine.index_dir, engine.collection_name)
    if use_cache:
        cached = _load_cached_facts(cache_key)
        if cached:
            if debug_label:
                _print_debug(cached, debug_label, intent)
            return cached

    fields: dict[str, BandoFactField] = {}
    for field_name, spec in FIELD_SPECS.items():
        retrieval = _retrieve_field(engine, spec)
        fields[field_name] = _build_field(spec, retrieval)

    fields["missing_or_uncertain_fields"] = _missing_field()
    all_sources: list[dict[str, Any]] = []
    for field_name in FACT_FIELD_ORDER:
        all_sources.extend(fields[field_name].sources)

    facts = BandoFacts(
        **fields,
        sources=_dedupe_sources(all_sources),
        cache_key=cache_key,
    )
    _write_cached_facts(facts)
    if debug_label:
        _print_debug(facts, debug_label, intent)
    return facts


def clear_bando_facts_cache() -> None:
    if FACTS_CACHE_PATH.exists():
        FACTS_CACHE_PATH.unlink()


def _field_value_text(field_value: list[str]) -> str:
    if not field_value:
        return INFO_NOT_RETRIEVED
    return "\n".join(f"- {value}" for value in field_value)


def _field_sources_text(sources: list[dict[str, Any]]) -> str:
    if not sources:
        return ""
    source_text = "; ".join(source["source"] for source in sources[:3])
    label = "Fonti" if len(sources[:3]) > 1 else "Fonte"
    return f"\n\n{label}: {source_text}"


def render_facts_debug(facts: BandoFacts) -> str:
    titles = {
        "title": "Titolo",
        "object": "Oggetto",
        "finality": "Finalita",
        "financial_allocation": "Dotazione finanziaria",
        "eligible_subjects": "Soggetti ammessi",
        "building_requirements": "Requisiti edificio",
        "deadline": "Termini",
        "submission_mode": "Modalita di presentazione",
        "required_documents": "Documentazione richiesta",
        "evaluation_criteria": "Criteri di valutazione",
        "post_award_obligations": "Obblighi successivi",
        "missing_or_uncertain_fields": "Informazioni da verificare",
    }
    parts = ["# Fatti estratti dal bando"]
    for field_name, fact_field in facts.iter_fields():
        parts.append(f"## {titles[field_name]}")
        parts.append(_field_value_text(fact_field.value))
        parts.append(
            f"\nChunk pertinenti: {fact_field.chunks} | "
            f"Fallback: {'si' if fact_field.fallback_used else 'no'}"
            if field_name != "missing_or_uncertain_fields"
            else ""
        )
        source_text = _field_sources_text(fact_field.sources)
        if source_text:
            parts.append(source_text)
    return normalize_visible_sources("\n\n".join(part for part in parts if part).strip())

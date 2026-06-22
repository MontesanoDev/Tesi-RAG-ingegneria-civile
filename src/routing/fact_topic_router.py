from enum import StrEnum
import re
import unicodedata


class FactTopic(StrEnum):
    TITLE = "title"
    OBJECT = "object"
    FINALITY = "finality"
    FINANCIAL_ALLOCATION = "financial_allocation"
    ELIGIBLE_SUBJECTS = "eligible_subjects"
    BUILDING_REQUIREMENTS = "building_requirements"
    DEADLINE = "deadline"
    SUBMISSION_MODE = "submission_mode"
    REQUIRED_DOCUMENTS = "required_documents"
    EVALUATION_CRITERIA = "evaluation_criteria"
    POST_AWARD_OBLIGATIONS = "post_award_obligations"
    MISSING_OR_UNCERTAIN_FIELDS = "missing_or_uncertain_fields"


TOPIC_PATTERNS: tuple[tuple[FactTopic, tuple[str, ...]], ...] = (
    (
        FactTopic.ELIGIBLE_SUBJECTS,
        (
            "soggetti ammessi",
            "chi puo partecipare",
            "chi presenta domanda",
            "chi puo fare domanda",
            "chi puo candidarsi",
            "beneficiari",
            "soggetti proponenti",
            "enti ammessi",
            "chi puo presentare",
        ),
    ),
    (
        FactTopic.DEADLINE,
        (
            "scadenza",
            "entro quando",
            "termine",
            "quando presentare",
            "data",
            "quando scade",
        ),
    ),
    (
        FactTopic.REQUIRED_DOCUMENTS,
        (
            "documenti",
            "allegati",
            "cosa devo trasmettere",
            "documentazione",
            "moduli",
            "cosa trasmettere",
            "quali atti",
        ),
    ),
    (
        FactTopic.FINANCIAL_ALLOCATION,
        (
            "dotazione",
            "importo",
            "finanziamento",
            "quanti soldi",
            "risorse",
            "budget",
            "quanto e",
        ),
    ),
    (
        FactTopic.EVALUATION_CRITERIA,
        (
            "criteri",
            "valutazione",
            "punteggio",
            "graduatoria",
            "soglia",
        ),
    ),
    (
        FactTopic.SUBMISSION_MODE,
        (
            "pec",
            "come presentare",
            "modalita",
            "invio",
            "come inviare",
            "come si presenta",
        ),
    ),
    (
        FactTopic.BUILDING_REQUIREMENTS,
        (
            "requisiti edificio",
            "edificio",
            "snaes",
            "anagrafe edilizia scolastica",
            "anagrafe regionale edilizia scolastica",
            "repertorio fabbisogno",
            "requisiti dell edificio",
            "requisiti immobile",
        ),
    ),
    (
        FactTopic.POST_AWARD_OBLIGATIONS,
        (
            "obblighi",
            "post concessione",
            "rendicontazione",
            "monitoraggio",
            "revoca",
            "cig",
            "gara",
            "dopo concessione",
            "successivi alla concessione",
        ),
    ),
    (
        FactTopic.MISSING_OR_UNCERTAIN_FIELDS,
        (
            "informazioni mancanti",
            "cosa manca",
            "da verificare",
            "dati mancanti",
            "campi mancanti",
        ),
    ),
    (
        FactTopic.FINALITY,
        (
            "finalita",
            "obiettivo",
            "scopo",
            "a cosa serve",
        ),
    ),
    (
        FactTopic.OBJECT,
        (
            "oggetto",
            "cosa riguarda",
            "di cosa tratta",
            "cosa finanzia",
        ),
    ),
    (
        FactTopic.TITLE,
        (
            "titolo",
            "nome del bando",
            "nome avviso",
            "che bando e",
        ),
    ),
)


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.strip().lower())
    without_accents = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    without_punctuation = re.sub(r"[^\w\s/]", " ", without_accents)
    return " ".join(without_punctuation.split())


def classify_fact_topic(message: str) -> str | None:
    normalized = _normalize(message)
    if not normalized:
        return None

    for topic, patterns in TOPIC_PATTERNS:
        if any(_normalize(pattern) in normalized for pattern in patterns):
            return topic.value
    return None


from enum import StrEnum
import re
import unicodedata


class Intent(StrEnum):
    GREETING = "greeting"
    COMPANY_PROFILE = "company_profile"
    CHECKLIST = "checklist"
    SUMMARY = "summary"
    DOCUMENT_QA = "document_qa"
    HELP = "unknown_help"
    COMMAND = "command"


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.strip().lower())
    without_accents = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    without_punctuation = re.sub(r"[^\w\s/]", " ", without_accents)
    return " ".join(without_punctuation.split())


def _contains_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(pattern in text for pattern in patterns)


def classify_intent(message: str) -> Intent:
    normalized = _normalize(message)
    if not normalized:
        return Intent.HELP

    if normalized.startswith("/"):
        if normalized == "/checklist":
            return Intent.CHECKLIST
        return Intent.COMMAND

    greeting_exact = {
        "ciao",
        "buongiorno",
        "buonasera",
        "ok",
        "okay",
        "grazie",
        "perfetto",
        "va bene",
    }
    if normalized in greeting_exact:
        return Intent.GREETING
    if normalized.startswith("grazie ") or normalized in {"ok grazie", "okay grazie"}:
        return Intent.GREETING

    company_patterns = (
        "chi siamo",
        "chi sono",
        "chi e mapi",
        "chi è mapi",
        "mapi ingegneria",
        "che azienda siamo",
        "che azienda sono",
        "nostro ruolo",
        "qual e il nostro ruolo",
        "qual e il profilo aziendale",
        "che dati aziendali",
        "dati aziendali abbiamo",
        "profilo aziendale",
    )
    if _contains_any(normalized, company_patterns):
        return Intent.COMPANY_PROFILE

    checklist_patterns = (
        "genera checklist",
        "generami checklist",
        "checklist candidatura",
        "checklist operativa",
        "cosa devo preparare",
        "cosa bisogna preparare",
        "preparare per partecipare",
        "documenti devo preparare",
        "partecipare al bando",
    )
    if _contains_any(normalized, checklist_patterns):
        return Intent.CHECKLIST

    summary_patterns = (
        "riassumi",
        "riassunto",
        "di cosa parla il bando",
        "spiegami il bando",
        "obiettivo del bando",
        "finalita del bando",
        "sintesi del bando",
        "fammi una sintesi",
    )
    if _contains_any(normalized, summary_patterns):
        return Intent.SUMMARY

    document_patterns = (
        "soggetti ammessi",
        "beneficiari",
        "requisiti",
        "scadenza",
        "termine",
        "allegati",
        "documenti",
        "documentazione",
        "dotazione finanziaria",
        "contributo",
        "finanziamento",
        "criteri",
        "valutazione",
        "punteggio",
        "pec",
        "istanza",
        "modalita",
        "rendicontazione",
        "revoca",
        "monitoraggio",
        "obblighi",
        "bando",
        "avviso",
    )
    question_starters = (
        "quali",
        "qual",
        "quando",
        "quanto",
        "come",
        "dove",
        "chi",
        "cosa",
    )
    if _contains_any(normalized, document_patterns):
        return Intent.DOCUMENT_QA
    if normalized.startswith(question_starters) and len(normalized.split()) >= 3:
        return Intent.DOCUMENT_QA

    return Intent.HELP

from enum import StrEnum

from src.routing.semantic_router import classify_message, normalize_message


class Intent(StrEnum):
    GREETING = "greeting"
    COMPANY_ELIGIBILITY = "company_eligibility"
    COMPANY_PROFILE = "company_profile"
    CHECKLIST = "checklist"
    SUMMARY = "summary"
    PARTICIPATION_STEPS = "participation_steps"
    DOCUMENT_QA = "document_qa"
    HELP = "unknown_help"
    COMMAND = "command"


def classify_intent(message: str) -> Intent:
    normalized = normalize_message(message)
    if normalized.startswith("/"):
        return Intent.COMMAND

    decision = classify_message(message)
    if decision.intent == "greeting":
        return Intent.GREETING
    if decision.intent == "company_eligibility":
        return Intent.COMPANY_ELIGIBILITY
    if decision.intent == "company_profile":
        return Intent.COMPANY_PROFILE
    if decision.intent == "summary":
        return Intent.SUMMARY
    if decision.intent == "participation_steps":
        return Intent.PARTICIPATION_STEPS
    if decision.intent in {"fact_qa", "document_qa"}:
        return Intent.DOCUMENT_QA
    return Intent.HELP

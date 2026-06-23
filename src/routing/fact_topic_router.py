from enum import StrEnum

from src.routing.semantic_router import classify_message


class FactTopic(StrEnum):
    ELIGIBLE_SUBJECTS = "eligible_subjects"
    BUILDING_REQUIREMENTS = "building_requirements"
    PARTICIPATION_REQUIREMENTS = "participation_requirements"
    DEADLINE = "deadline"
    SUBMISSION_MODE = "submission_mode"
    REQUIRED_DOCUMENTS = "required_documents"
    FINANCIAL_ALLOCATION = "financial_allocation"
    EVALUATION_CRITERIA = "evaluation_criteria"
    POST_AWARD_OBLIGATIONS = "post_award_obligations"
    MISSING_INFORMATION = "missing_information"


def classify_fact_topic(message: str) -> str | None:
    decision = classify_message(message)
    if decision.fact_topic == "none":
        return None
    return decision.fact_topic

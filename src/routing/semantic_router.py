from __future__ import annotations

import json
import os
import re
import unicodedata
from typing import Any, Literal, get_args

from llama_index.core import Settings
from pydantic import BaseModel, Field, ValidationError


IntentLiteral = Literal[
    "greeting",
    "company_eligibility",
    "company_profile",
    "summary",
    "participation_steps",
    "fact_qa",
    "document_qa",
    "help",
]

FactTopicLiteral = Literal[
    "none",
    "eligible_subjects",
    "building_requirements",
    "participation_requirements",
    "submission_package",
    "deadline",
    "submission_mode",
    "required_documents",
    "financial_allocation",
    "evaluation_criteria",
    "post_award_obligations",
    "missing_information",
]


class RouterDecision(BaseModel):
    intent: IntentLiteral
    fact_topic: FactTopicLiteral = "none"
    fact_topics: list[FactTopicLiteral] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reason: str = ""
    source: str = ""
    fallback_to_rag: bool = False


VALID_INTENTS = set(get_args(IntentLiteral))
VALID_FACT_TOPICS = set(get_args(FactTopicLiteral))

PURE_GREETINGS = {
    "ciao",
    "buongiorno",
    "buonasera",
    "salve",
    "grazie",
    "ok",
    "okay",
    "perfetto",
}

STOPWORDS = {
    "a",
    "ad",
    "al",
    "alla",
    "allo",
    "ai",
    "agli",
    "alle",
    "che",
    "chi",
    "come",
    "con",
    "cosa",
    "da",
    "dal",
    "dalla",
    "de",
    "dei",
    "del",
    "della",
    "di",
    "e",
    "gli",
    "i",
    "il",
    "in",
    "la",
    "le",
    "lo",
    "mi",
    "nel",
    "per",
    "qual",
    "quale",
    "quali",
    "sono",
    "su",
    "un",
    "una",
}

INTENT_DESCRIPTIONS = {
    "company_eligibility": "domanda se MAPI, noi o la nostra azienda puo essere soggetto ammesso, soggetto proponente, partecipare, candidarsi o presentare domanda",
    "company_profile": "richiesta su MAPI Ingegneria, profilo aziendale, chi siamo, azienda, ruolo o dati aziendali",
    "summary": "richiesta di riassunto, sintesi, panoramica o spiegazione generale del bando",
    "participation_steps": "richiesta operativa su come partecipare, candidarsi, presentare domanda, preparare la candidatura o seguire la procedura",
    "fact_qa": "domanda puntuale su un fatto strutturato del bando presente nei BandoFacts",
    "document_qa": "domanda sul documento non riconducibile a un campo strutturato dei BandoFacts",
    "help": "messaggio non comprensibile o non classificabile",
}

FACT_TOPIC_DESCRIPTIONS = {
    "eligible_subjects": "soggetti ammessi, enti proponenti, beneficiari, chi puo partecipare",
    "building_requirements": "requisiti specifici dell'edificio, immobile, scuola, SNAES, anagrafe edilizia scolastica, repertorio",
    "participation_requirements": "requisiti complessivi di partecipazione e ammissibilita, soggetto proponente, edificio e informazioni da verificare",
    "submission_package": "documenti, allegati, cosa trasmettere, modalita di invio e scadenza entro cui presentare la domanda",
    "deadline": "scadenza, termine, data limite, entro quando presentare la domanda",
    "submission_mode": "modalita di presentazione, invio, PEC, come trasmettere o presentare l'istanza",
    "required_documents": "documentazione richiesta, documenti, allegati, moduli, cosa trasmettere",
    "financial_allocation": "dotazione finanziaria, importo, risorse, finanziamento, budget",
    "evaluation_criteria": "criteri di valutazione, punteggio, graduatoria, soglia minima",
    "post_award_obligations": "obblighi successivi alla concessione, rendicontazione, monitoraggio, revoca, CIG, gara",
    "missing_information": "informazioni mancanti o da verificare nello scenario, dati tecnici e documenti disponibili",
}

TOPIC_PRIORITY = (
    "participation_requirements",
    "eligible_subjects",
    "building_requirements",
    "deadline",
    "submission_mode",
    "required_documents",
    "financial_allocation",
    "evaluation_criteria",
    "post_award_obligations",
    "missing_information",
)

INTENT_PRIORITY = (
    "participation_steps",
    "company_profile",
    "summary",
)

CLASSIFIER_PROMPT = """Sei un semantic router per una demo Chainlit + RAG su un bando pubblico.

Devi classificare il messaggio utente. Non rispondere alla domanda.
Restituisci solo un oggetto JSON valido con queste chiavi:
- intent
- fact_topic
- confidence
- reason

Intent disponibili:
- greeting: saluto o ringraziamento puro.
- company_eligibility: domanda se MAPI, noi o la nostra azienda puo' partecipare, candidarsi, presentare domanda o essere soggetto proponente/ammesso nel bando.
- company_profile: domanda su MAPI Ingegneria, azienda, ruolo o profilo.
- summary: richiesta di riassunto o panoramica del bando.
- participation_steps: l'utente chiede cosa fare per partecipare, candidarsi o presentare domanda.
- fact_qa: l'utente chiede un'informazione puntuale coperta dai BandoFacts.
- document_qa: domanda documentale non coperta dai BandoFacts.
- help: richiesta veramente incomprensibile.

Fact topic disponibili:
- none
- eligible_subjects
- building_requirements
- participation_requirements
- submission_package
- deadline
- submission_mode
- required_documents
- financial_allocation
- evaluation_criteria
- post_award_obligations
- missing_information

Regole:
- Usa company_eligibility quando la domanda combina MAPI/noi/azienda con ammissibilita', candidatura, presentazione domanda, partecipazione, soggetto proponente o soggetto ammesso.
- Usa fact_qa/submission_package quando la domanda combina documenti/allegati/cosa mandare con scadenza/entro quando/termine.
- Usa participation_steps quando l'utente chiede cosa fare per partecipare/candidarsi/presentare domanda.
- Usa fact_qa quando l'utente chiede un'informazione puntuale del bando gia' rappresentata da un fact_topic.
- Usa participation_requirements per richieste generiche sui requisiti di partecipazione/ammissibilita.
- Usa document_qa solo quando la domanda non e' coperta dai fact_topic.
- Usa help solo se la richiesta e' davvero incomprensibile.
- Se intent e' company_eligibility, fact_topic deve essere eligible_subjects.
- Se intent non e' fact_qa, participation_steps o company_eligibility, fact_topic deve essere none.

Esempi concettuali:
- "MAPI puo' presentare domanda direttamente?" -> company_eligibility / eligible_subjects
- "Noi possiamo candidarci?" -> company_eligibility / eligible_subjects
- "come partecipo al bando?" -> participation_steps / participation_requirements
- "requisiti?" -> fact_qa / participation_requirements
- "quali sono i soggetti ammessi?" -> fact_qa / eligible_subjects
- "qual e' la scadenza?" -> fact_qa / deadline
- "documenti da trasmettere?" -> fact_qa / required_documents
- "cosa devo mandare e entro quando?" -> fact_qa / submission_package
- "riassumi il bando" -> summary / none
- "chi siamo?" -> company_profile / none

Messaggio utente:
{message}
"""


def normalize_message(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.strip().lower())
    without_accents = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    without_punctuation = re.sub(r"[^\w\s/]", " ", without_accents)
    return " ".join(without_punctuation.split())


def _tokens(text: str) -> list[str]:
    normalized = normalize_message(text)
    return [
        token
        for token in normalized.split()
        if len(token) > 1 and token not in STOPWORDS
    ]


def _stem(token: str) -> str:
    for suffix in (
        "mente",
        "zione",
        "zioni",
        "arsi",
        "armi",
        "are",
        "ere",
        "ire",
        "iamo",
        "ano",
        "ono",
        "ato",
        "ata",
        "ati",
        "ate",
        "o",
        "i",
        "a",
        "e",
    ):
        if len(token) > len(suffix) + 3 and token.endswith(suffix):
            return token[: -len(suffix)]
    return token


def _semantic_tokens(text: str) -> set[str]:
    return {_stem(token) for token in _tokens(text)}


def _score(message: str, description: str) -> float:
    message_tokens = _semantic_tokens(message)
    description_tokens = _semantic_tokens(description)
    if not message_tokens or not description_tokens:
        return 0.0
    overlap = message_tokens & description_tokens
    return len(overlap) / max(len(message_tokens), 1)


def _is_pure_greeting(message: str) -> bool:
    tokens = _tokens(message)
    return bool(tokens) and len(tokens) <= 3 and all(token in PURE_GREETINGS for token in tokens)


def _is_company_eligibility(message: str) -> bool:
    normalized = normalize_message(message)
    tokens = set(normalized.split())
    if not tokens:
        return False

    has_company_context = bool(
        {"mapi", "noi", "azienda", "possiamo"} & tokens
    ) or "nostra azienda" in normalized
    if not has_company_context:
        return False

    if any(
        phrase in normalized
        for phrase in (
            "presentare domanda",
            "presenta domanda",
            "presentare direttamente domanda",
            "soggetto proponente",
            "soggetto ammesso",
            "soggetti ammessi",
        )
    ):
        return True

    has_participation_term = any(
        token.startswith(("partecip", "candid", "ammess", "ammissibil"))
        for token in tokens
    )
    has_submission_term = "domanda" in tokens and any(
        token.startswith("present") for token in tokens
    )
    return has_participation_term or has_submission_term


def _is_scenario_clarification(message: str) -> bool:
    normalized = normalize_message(message)
    tokens = set(normalized.split())
    if not tokens:
        return False

    company_context = bool(
        {
            "mapi",
            "azienda",
            "nostro",
            "nostra",
            "noi",
            "proponente",
            "soggetto",
            "presenta",
            "presentare",
        }
        & tokens
    ) or "chi presenta" in normalized
    building_context = bool(
        {"edificio", "immobile", "scuola", "snaes", "requisiti"} & tokens
    )
    comparison_context = (
        " o " in f" {normalized} "
        or "oppure" in tokens
        or {"problema", "vincolo", "conta", "livello"} & tokens
        or "di piu" in normalized
    )
    return company_context and building_context and bool(comparison_context)


def _is_submission_package(message: str) -> bool:
    normalized = normalize_message(message)
    tokens = set(normalized.split())
    if not tokens:
        return False

    has_document_context = any(
        token.startswith(("document", "allegat", "mand", "trasmett", "invi", "predispon"))
        for token in tokens
    )
    has_time_context = (
        "entro quando" in normalized
        or "entro" in tokens
        or "quando" in tokens
        or any(token.startswith(("scadenz", "termin")) for token in tokens)
    )
    return has_document_context and has_time_context


def _is_participation_followup(message: str) -> bool:
    normalized = normalize_message(message)
    tokens = set(normalized.split())
    if not tokens:
        return False
    has_operational_context = (
        "prime cose" in normalized
        or "cose da verificare" in normalized
        or "da verificare" in normalized
    )
    has_attempt_context = bool(
        {"provarci", "volessimo", "domani", "procedere"} & tokens
    )
    return has_operational_context and has_attempt_context


def _is_building_requirement_question(message: str) -> bool:
    normalized = normalize_message(message)
    tokens = set(normalized.split())
    if "snaes" in tokens:
        return True
    return bool({"progetto", "codice"} <= tokens and {"posto", "apposto"} & tokens)


def _priority_rule_decision(message: str) -> RouterDecision | None:
    normalized = normalize_message(message)
    if not normalized:
        return RouterDecision(
            intent="help",
            fact_topic="none",
            confidence=0.0,
            reason="Messaggio vuoto.",
        )

    if _is_pure_greeting(message):
        return RouterDecision(
            intent="greeting",
            fact_topic="none",
            confidence=0.95,
            reason="Saluto o ringraziamento puro.",
        )

    if _is_company_eligibility(message):
        return RouterDecision(
            intent="company_eligibility",
            fact_topic="eligible_subjects",
            confidence=0.94,
            reason="Domanda su ammissibilita' di MAPI o dell'azienda nello scenario.",
            source="BandoFacts + company_profile + ScenarioFacts",
            fallback_to_rag=False,
        )

    if _is_scenario_clarification(message):
        return RouterDecision(
            intent="fact_qa",
            fact_topic="participation_requirements",
            fact_topics=["eligible_subjects", "building_requirements"],
            confidence=0.9,
            reason="Chiarimento comparativo tra soggetto proponente e requisiti dell'edificio.",
            source="BandoFacts + ScenarioFacts + company_profile",
            fallback_to_rag=False,
        )

    if _is_submission_package(message):
        return RouterDecision(
            intent="fact_qa",
            fact_topic="submission_package",
            fact_topics=["required_documents", "deadline", "submission_mode"],
            confidence=0.9,
            reason="Domanda combinata su documenti da trasmettere, modalita e scadenza.",
            source="BandoFacts",
            fallback_to_rag=False,
        )

    if _is_participation_followup(message):
        return RouterDecision(
            intent="participation_steps",
            fact_topic="participation_requirements",
            confidence=0.88,
            reason="Follow-up operativo sulle prime verifiche per procedere.",
            source="BandoFacts",
            fallback_to_rag=False,
        )

    if _is_building_requirement_question(message):
        return RouterDecision(
            intent="fact_qa",
            fact_topic="building_requirements",
            fact_topics=["building_requirements"],
            confidence=0.88,
            reason="Domanda sui requisiti dell'edificio o sul codice SNAES.",
            source="BandoFacts",
            fallback_to_rag=False,
        )

    return None


def _extract_json_object(text: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(text)
        return payload if isinstance(payload, dict) else None
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _coerce_decision(payload: dict[str, Any], fallback_reason: str) -> RouterDecision:
    intent = str(payload.get("intent") or "").strip().lower()
    fact_topic = str(payload.get("fact_topic") or "none").strip().lower()
    fact_topics = [
        str(topic).strip().lower()
        for topic in payload.get("fact_topics", [])
        if str(topic).strip().lower() in VALID_FACT_TOPICS
    ]
    source = str(payload.get("source") or "").strip()
    fallback_to_rag = bool(payload.get("fallback_to_rag", False))

    if intent not in VALID_INTENTS:
        intent = "document_qa"
    if fact_topic not in VALID_FACT_TOPICS:
        fact_topic = "none"

    if intent == "company_eligibility":
        fact_topic = "eligible_subjects"
        source = "BandoFacts + company_profile + ScenarioFacts"
        fallback_to_rag = False
    elif intent == "fact_qa" and fact_topic == "submission_package":
        fact_topics = ["required_documents", "deadline", "submission_mode"]
        source = "BandoFacts"
        fallback_to_rag = False
    elif intent == "participation_steps" and fact_topic == "none":
        fact_topic = "participation_requirements"
    elif intent != "fact_qa" and intent != "participation_steps":
        fact_topic = "none"
    elif intent == "fact_qa" and fact_topic == "none":
        intent = "document_qa"

    try:
        confidence = float(payload.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))
    reason = str(payload.get("reason") or fallback_reason).strip()

    try:
        return RouterDecision(
            intent=intent,
            fact_topic=fact_topic,
            fact_topics=fact_topics,
            confidence=confidence,
            reason=reason,
            source=source,
            fallback_to_rag=fallback_to_rag,
        )
    except ValidationError:
        return RouterDecision(
            intent="document_qa",
            fact_topic="none",
            confidence=0.0,
            reason=fallback_reason,
            fallback_to_rag=True,
        )


def _classify_with_llm(message: str) -> RouterDecision | None:
    if os.getenv("SEMANTIC_ROUTER_DISABLE_LLM") == "1":
        return None

    try:
        from src.retrieval.rag_engine import configure_llm

        configure_llm()
        prompt = CLASSIFIER_PROMPT.format(message=message.strip())
        try:
            response = Settings.llm.complete(
                prompt,
                response_format={"type": "json_object"},
            )
        except TypeError:
            response = Settings.llm.complete(prompt)
        payload = _extract_json_object(str(response))
        if payload is None:
            return None
        return _coerce_decision(payload, "Classificazione LLM JSON.")
    except Exception:
        return None


def _best_topic(message: str) -> tuple[str, float]:
    scored = {
        topic: _score(message, description)
        for topic, description in FACT_TOPIC_DESCRIPTIONS.items()
    }
    best_topic = max(
        TOPIC_PRIORITY,
        key=lambda topic: (scored.get(topic, 0.0), -TOPIC_PRIORITY.index(topic)),
    )
    return best_topic, scored.get(best_topic, 0.0)


def _fallback_classify(message: str) -> RouterDecision:
    priority_decision = _priority_rule_decision(message)
    if priority_decision is not None:
        return priority_decision

    intent_scores = {
        intent: _score(message, description)
        for intent, description in INTENT_DESCRIPTIONS.items()
        if intent not in {"fact_qa", "document_qa", "help"}
    }
    best_intent = max(
        INTENT_PRIORITY,
        key=lambda intent: (intent_scores.get(intent, 0.0), -INTENT_PRIORITY.index(intent)),
    )
    best_intent_score = intent_scores[best_intent]

    topic, topic_score = _best_topic(message)

    if best_intent == "participation_steps" and best_intent_score > 0:
        return RouterDecision(
            intent="participation_steps",
            fact_topic="participation_requirements",
            confidence=min(0.9, 0.58 + best_intent_score),
            reason="Richiesta operativa di partecipazione/candidatura.",
        )

    if best_intent_score > 0 and best_intent in {"company_profile", "summary"}:
        return RouterDecision(
            intent=best_intent,
            fact_topic="none",
            confidence=min(0.9, 0.55 + best_intent_score),
            reason=f"Richiesta associata all'intent {best_intent}.",
        )

    if topic_score > 0:
        return RouterDecision(
            intent="fact_qa",
            fact_topic=topic,
            confidence=min(0.88, 0.52 + topic_score),
            reason=f"Domanda puntuale associata al topic {topic}.",
        )

    if "?" in message or len(_tokens(message)) >= 2:
        return RouterDecision(
            intent="document_qa",
            fact_topic="none",
            confidence=0.45,
            reason="Domanda documentale non coperta dai topic strutturati.",
        )

    return RouterDecision(
        intent="help",
        fact_topic="none",
        confidence=0.2,
        reason="Richiesta troppo breve o non classificabile.",
    )


def classify_message(message: str) -> RouterDecision:
    priority_decision = _priority_rule_decision(message)
    if priority_decision is not None:
        return priority_decision

    llm_decision = _classify_with_llm(message)
    if llm_decision is not None:
        return llm_decision
    return _fallback_classify(message)

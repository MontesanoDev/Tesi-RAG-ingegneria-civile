import unittest
import os

os.environ["SEMANTIC_ROUTER_DISABLE_LLM"] = "1"

from src.routing.command_router import normalize_explicit_command
from src.routing.semantic_router import classify_message


class RoutingTest(unittest.TestCase):
    def test_command_aliases(self):
        self.assertEqual(normalize_explicit_command("/index"), "/index")
        self.assertEqual(normalize_explicit_command("index"), "/index")
        self.assertEqual(normalize_explicit_command("", "index"), "/index")
        self.assertEqual(normalize_explicit_command("checklist"), "/checklist")

    def test_base_intents(self):
        self.assertEqual(classify_message("ciao").intent, "greeting")
        self.assertEqual(classify_message("chi siamo?").intent, "company_profile")
        self.assertEqual(classify_message("riassumi il bando").intent, "summary")

    def test_participation_steps_intent(self):
        decision = classify_message("come partecipo al bando?")
        self.assertEqual(decision.intent, "participation_steps")
        self.assertEqual(decision.fact_topic, "participation_requirements")

    def test_company_eligibility_intent(self):
        for message in (
            "MAPI può presentare domanda direttamente?",
            "MAPI può partecipare al bando?",
            "Noi possiamo candidarci?",
            "La nostra azienda è ammessa?",
            "Possiamo essere soggetto proponente?",
            "MAPI è un soggetto ammesso?",
        ):
            with self.subTest(message=message):
                decision = classify_message(message)
                self.assertEqual(decision.intent, "company_eligibility")
                self.assertEqual(decision.fact_topic, "eligible_subjects")
                self.assertEqual(
                    decision.source,
                    "BandoFacts + company_profile + ScenarioFacts",
                )
                self.assertFalse(decision.fallback_to_rag)

        self.assertEqual(classify_message("chi siamo?").intent, "company_profile")

    def test_fact_qa_topics(self):
        decision = classify_message("requisiti?")
        self.assertEqual(decision.intent, "fact_qa")
        self.assertEqual(decision.fact_topic, "participation_requirements")

        decision = classify_message("quali sono i soggetti ammessi?")
        self.assertEqual(decision.intent, "fact_qa")
        self.assertEqual(decision.fact_topic, "eligible_subjects")

        decision = classify_message("qual è la scadenza?")
        self.assertEqual(decision.intent, "fact_qa")
        self.assertEqual(decision.fact_topic, "deadline")

        decision = classify_message("quali documenti devo trasmettere?")
        self.assertEqual(decision.intent, "fact_qa")
        self.assertEqual(decision.fact_topic, "required_documents")

        decision = classify_message("quali sono i criteri di valutazione?")
        self.assertEqual(decision.intent, "fact_qa")
        self.assertEqual(decision.fact_topic, "evaluation_criteria")

        decision = classify_message("qual è la dotazione finanziaria?")
        self.assertEqual(decision.intent, "fact_qa")
        self.assertEqual(decision.fact_topic, "financial_allocation")

    def test_required_routing_regressions(self):
        self.assertEqual(
            classify_message("ok come partecipo?").intent,
            "participation_steps",
        )
        self.assertEqual(
            classify_message("Non ho capito quando termina").fact_topic,
            "deadline",
        )
        self.assertEqual(classify_message("riassumi il bando").intent, "summary")
        self.assertEqual(
            classify_message("quali sono i soggetti ammessi?").fact_topic,
            "eligible_subjects",
        )
        self.assertEqual(
            classify_message(
                "MAPI può presentare domanda direttamente oppure serve per forza un ente locale?"
            ).intent,
            "company_eligibility",
        )
        self.assertEqual(
            classify_message(
                "Ok, quindi se volessimo provarci domani, quali sono le prime cose da verificare?"
            ).intent,
            "participation_steps",
        )
        self.assertEqual(
            classify_message(
                "Se abbiamo solo il progetto ma non il codice SNAES, siamo a posto?"
            ).fact_topic,
            "building_requirements",
        )

    def test_scenario_clarification_routes_to_facts(self):
        for message in (
            "Non ho capito: il problema è l’azienda o l’edificio?",
            "È un problema nostro o dell’edificio?",
            "Il vincolo è su MAPI o sulla scuola?",
            "Conta di più chi presenta o l’immobile?",
        ):
            with self.subTest(message=message):
                decision = classify_message(message)
                self.assertEqual(decision.intent, "fact_qa")
                self.assertEqual(decision.fact_topic, "participation_requirements")
                self.assertIn("eligible_subjects", decision.fact_topics)
                self.assertIn("building_requirements", decision.fact_topics)
                self.assertFalse(decision.fallback_to_rag)

    def test_submission_package_routes_to_multi_topic_fact_qa(self):
        decision = classify_message(
            "Mi manca solo capire cosa devo mandare e entro quando."
        )
        self.assertEqual(decision.intent, "fact_qa")
        self.assertEqual(decision.fact_topic, "submission_package")
        self.assertIn("required_documents", decision.fact_topics)
        self.assertIn("deadline", decision.fact_topics)
        self.assertIn("submission_mode", decision.fact_topics)
        self.assertFalse(decision.fallback_to_rag)


if __name__ == "__main__":
    unittest.main()

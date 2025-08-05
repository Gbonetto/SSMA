from .base import Agent

class PlannerAgent(Agent):
    """Agent de planification.
    Analyse la question et propose un ordre d'exécution des autres agents.
    """
    def can_handle(self, question: str, context: dict) -> bool:
        # Le planner est consulté systématiquement.
        return True

    async def run(self, question: str, context: dict) -> dict:
        intention = context.get("intention", "")
        q = question.lower()
        plan: list[str] = []
        reasoning_parts: list[str] = []

        entity_keywords = ("entit", "montant", "date", "personne", "extrait", "extraire", "noms", "entreprise")
        if any(kw in intention for kw in entity_keywords) or any(kw in q for kw in entity_keywords):
            plan.append("ExtractionAgent")
            reasoning_parts.append("Orientation extraction d'entités.")

        if "feedback:" in q:
            plan.append("FeedbackAgent")
            reasoning_parts.append("Demande de feedback détectée.")

        if "n8n" in q:
            plan.append("N8NWebhookAgent")
            reasoning_parts.append("Webhook n8n requis.")

        # Ajoute toujours une recherche puis une synthèse par défaut
        if "SearchAgent" not in plan:
            plan.append("SearchAgent")
            reasoning_parts.append("Recherche nécessaire pour trouver des sources.")
        if "SynthesisAgent" not in plan:
            plan.append("SynthesisAgent")
            reasoning_parts.append("Synthèse finale pour répondre.")

        reasoning = " ".join(reasoning_parts)
        return {"plan": plan, "reasoning": reasoning}

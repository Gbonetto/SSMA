# agents/agent_search.py
from .base import Agent
from pipelines.hybrid_retrieval import hybrid_search

MIN_CONFIDENCE = 1.2  # Ajuste ce seuil aprÃ¨s test terrain, 1.2/1.5/2 selon le modÃ¨le

class SearchAgent(Agent):
    def can_handle(self, question: str, context: dict) -> bool:
        q = question.lower()
        keywords = ["trouve", "cherche", "mot-clÃ©", "passage", "extrait", "article", "page"]
        return any(kw in q for kw in keywords) or context.get("force_search", False)

    async def run(self, question: str, context: dict) -> dict:
        top_k = context.get("top_k", 7)
        search_results = hybrid_search(question, top_k=top_k)

        # Ajoute les scores arrondis pour l'UI
        for res in search_results:
            score = res.get("rerank_score")
            if score is not None:
                res["score"] = round(score, 4)

        # Si aucun rÃ©sultat ou confiance trop basse, ne pas halluciner :
        if not search_results or search_results[0].get("rerank_score", 0) < MIN_CONFIDENCE:
            context["sources"] = []
            return {
                "answer": "Aucun passage rÃ©ellement pertinent nâ€™a Ã©tÃ© trouvÃ© dans vos documents.",
                "sources": [],
                "entities": {}
            }

        # Sinon, push dans le contexte pour extraction dâ€™entitÃ©s, synthÃ¨se, etc.
        context["sources"] = search_results

        return {
            "answer": "RÃ©sultats rerankÃ©s et pertinents (mode SearchAgent)",
            "sources": search_results,
            "entities": {}
        }




from .base import Agent
from pipelines.extract_entities import extract_all_entities
from core.config import settings

class ExtractionAgent(Agent):
    def can_handle(self, question: str, context: dict) -> bool:
        q = question.lower()
        return any(kw in q for kw in [
            "montant", "date", "personne", "personnes citÃ©es", "entreprise", "entreprises citÃ©es",
            "extrait les entitÃ©s", "extraction", "qui sont"
        ])

    async def run(self, question: str, context: dict) -> dict:
        # 1. Extraction sur tout le doc si demandÃ©
        use_full_doc = context.get("extract_on_full_doc", False)
        full_doc_text = context.get("full_document_text")

        if use_full_doc and full_doc_text:
            text = full_doc_text
            sources = context.get("sources", [])
        else:
            sources = context.get("sources", [])
            if not sources:
                # Recherche automatique si pas de sources dans le contexte
                from agents.agent_search import SearchAgent
                search_results = await SearchAgent().run(question, context)
                sources = search_results.get("sources", [])
                context["sources"] = sources
            text = "\n".join(s.get("text", "") for s in sources if s)

        # 2. Extraction dâ€™entitÃ©s avancÃ©e (spaCy + regex + fallback LLM OpenAI si dispo)
        entities = extract_all_entities(
            text,
            openai_api_key=getattr(settings, "OPENAI_API_KEY", None),
            fallback_llm=None,  # Plug ici une fonction LLM si tu veux du RAG propriÃ©taire
            filter_result=True
        )

        # 3. Construction d'une rÃ©ponse textuelle explicite, + downstream structurÃ©
        response_parts = []
        if entities.get("PER"):
            response_parts.append(f"Personnes citÃ©es : {', '.join(entities['PER'])}")
        if entities.get("ORG"):
            response_parts.append(f"Organisations citÃ©es : {', '.join(entities['ORG'])}")
        if entities.get("montants"):
            response_parts.append(f"Montants trouvÃ©s : {', '.join(entities['montants'])}")
        if entities.get("dates"):
            response_parts.append(f"Dates trouvÃ©es : {', '.join(entities['dates'])}")
        if not response_parts:
            answer = "Aucune entitÃ© significative n'a Ã©tÃ© dÃ©tectÃ©e dans les documents."
        else:
            answer = ". ".join(response_parts) + "."

        # 4. Retourne la rÃ©ponse textuelle + entitÃ©s prÃªtes Ã  l'exploitation (n8n, analytics, etc.)
        return {
            "answer": answer,
            "sources": sources,
            "entities": entities
        }




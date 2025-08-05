# agents/agent_synthesis.py
from .base import Agent
from pipelines.rag_chain import answer_with_rag

class SynthesisAgent(Agent):
    """
    Agent principal pour la RAG : synthÃ¨se et rÃ©ponses via LangChain + Qdrant.
    """
    def can_handle(self, question: str, context: dict) -> bool:
        # Pour lâ€™instant, remonte toujours en premier
        return True

    async def run(self, question: str, context: dict) -> dict:
        # top_k / user peuvent venir du context
        top_k = context.get("top_k", 5)
        user = context.get("user")
        result = answer_with_rag(question, top_k=top_k, user=user)
        # MAJ context avec les sources pour exploitation par ExtractionAgent
        context["sources"] = result.get("sources", [])
        return result




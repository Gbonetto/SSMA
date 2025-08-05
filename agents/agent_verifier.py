"""Verification agent relying on the auto evaluation pipeline."""

from .base import Agent
from pipelines.auto_eval import auto_eval_llm

class VerifierAgent(Agent):
    """Run a post-generation evaluation on the last answer."""

    def can_handle(self, question: str, context: dict) -> bool:
        """The verifier can run when an answer is available in context."""
        return bool(context.get("last_answer"))

    async def run(self, question: str, context: dict) -> dict:
        """Execute automatic evaluation and return the score."""
        answer = context.get("last_answer")
        sources = context.get("sources", [])
        if not answer:
            return {"auto_eval": {}}
        eval_result = auto_eval_llm(question, answer, sources)
        context["auto_eval"] = eval_result
        return {
            "answer": answer,
            "sources": sources,
            "entities": {},
            "auto_eval": eval_result,
        }

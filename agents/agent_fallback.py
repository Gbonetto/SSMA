from .base import Agent


class FallbackAgent(Agent):
    """Agent de repli final utilisé lorsque les autres échouent."""

    def can_handle(self, question: str, context: dict) -> bool:
        # S'exécute toujours en dernier recours
        return True

    async def run(self, question: str, context: dict) -> dict:
        return {
            "answer": "Désolé, je ne sais pas répondre.",
            "sources": [],
            "entities": {}
        }

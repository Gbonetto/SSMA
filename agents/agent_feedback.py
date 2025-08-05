from .base import Agent
from core.logging import log_feedback

class FeedbackAgent(Agent):
    def can_handle(self, question: str, context: dict) -> bool:
        # Feedback doit commencer par "feedback:"
        return question.lower().startswith("feedback:")

    async def run(self, question: str, context: dict) -> dict:
        """
        Format attendu :
            feedback:<answer_id>:<statut>:<commentaire>
            Exemple : feedback:abc123:utile:Bonne réponse !
        """
        parts = question.split(":", 3)
        if len(parts) != 4:
            return {
                "answer": (
                    "Format de feedback incorrect. Utilise : "
                    "feedback:<answer_id>:<utile|inutile>:<commentaire>"
                )
            }
        _, answer_id, status, comment = parts
        status = status.lower()
        if status not in ["utile", "inutile"]:
            return {"answer": "Statut de feedback non reconnu (utile|inutile autorisés)"}
        user = context.get("user", "anonymous")
        log_feedback(answer_id, status, comment, user)
        return {"answer": f"Feedback reçu pour {answer_id} ({status})"}




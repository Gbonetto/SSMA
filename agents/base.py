# agents/base.py
from abc import ABC, abstractmethod

class Agent(ABC):
    @abstractmethod
    def can_handle(self, question: str, context: dict) -> bool:
        """
        Retourne True si cet agent doit prendre en charge la question.
        """
        pass

    @abstractmethod
    async def run(self, question: str, context: dict) -> dict:
        """
        Exécute la logique de l’agent et retourne un dict :
        {
          "answer": str,
          "sources": list[dict],
          "entities": dict
        }
        """
        pass




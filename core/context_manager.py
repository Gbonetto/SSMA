# core/context_manager.py

from typing import Dict, Any, List, Optional

class ContextManager:
    """
    ContextManager Excellence+ pour SMA-RAG :
    - Historique des questions (multi-session)
    - Gestion et fusion des entitÃ©s extraites
    - RÃ©sumÃ©s contextuels (pour long memory ou synthÃ¨se)
    - Variables temporaires par session (user, top_k, flags, etc.)
    - DerniÃ¨res sources trouvÃ©es (pour extraction, rerank, feedback)
    - Stockage du texte complet du doc (pour extraction full-doc)
    """

    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def get(self, session_id: str, question: Optional[str] = None) -> Dict[str, Any]:
        """
        RÃ©cupÃ¨re/crÃ©e un contexte de session.
        Ajoute la question Ã  l'historique si fournie.
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "history": [],
                "entities": {},
                "context_summaries": [],
                "vars": {},
                "sources": [],
                "full_document_text": None
            }
        session = self.sessions[session_id]
        if question:
            session["history"].append(question)
        return session

    # EntitÃ©s : gestion avancÃ©e
    def set_entity(self, session_id: str, key: str, value: Any):
        ctx = self.get(session_id)
        ctx["entities"][key] = value

    def add_entities(self, session_id: str, entities: Dict[str, Any]):
        ctx = self.get(session_id)
        for k, v in entities.items():
            if k in ctx["entities"] and isinstance(ctx["entities"][k], list) and isinstance(v, list):
                # Fusionne et dÃ©duplique (liste)
                ctx["entities"][k] = list(set(ctx["entities"][k] + v))
            else:
                ctx["entities"][k] = v

    def clear_entities(self, session_id: str):
        ctx = self.get(session_id)
        ctx["entities"] = {}

    # RÃ©sumÃ©s de contexte (long memory, synthÃ¨ses)
    def add_context_summary(self, session_id: str, summary: str):
        ctx = self.get(session_id)
        ctx["context_summaries"].append(summary)

    def get_context_summaries(self, session_id: str) -> List[str]:
        ctx = self.get(session_id)
        return ctx["context_summaries"]

    # Variables temporaires par session
    def set_var(self, session_id: str, key: str, value: Any):
        ctx = self.get(session_id)
        ctx["vars"][key] = value

    def get_var(self, session_id: str, key: str, default=None):
        ctx = self.get(session_id)
        return ctx["vars"].get(key, default)

    # Gestion des sources
    def set_sources(self, session_id: str, sources: List[Dict[str, Any]]):
        ctx = self.get(session_id)
        ctx["sources"] = sources

    def get_sources(self, session_id: str) -> List[Dict[str, Any]]:
        ctx = self.get(session_id)
        return ctx.get("sources", [])

    def clear_sources(self, session_id: str):
        ctx = self.get(session_id)
        ctx["sources"] = []

    # Texte complet du document (pour extraction globale)
    def set_full_document_text(self, session_id: str, text: str):
        ctx = self.get(session_id)
        ctx["full_document_text"] = text

    def get_full_document_text(self, session_id: str) -> Optional[str]:
        ctx = self.get(session_id)
        return ctx.get("full_document_text")

    # Reset total d'une session (purge tout)
    def clear(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]




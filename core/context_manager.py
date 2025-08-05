"""Context management and storage backends.

This module introduces a ``BaseContextStore`` interface with two concrete
implementations:

``InMemoryContextStore``
    Simple Python ``dict`` based storage.

``SQLContextStore``
    Persistent storage using SQLAlchemy (SQLite by default).

The ``ContextManager`` class operates on a ``BaseContextStore`` instance and
exposes high level helpers for manipulating session context such as history,
entities and sources.  The backend in use is determined by the application
settings (see :mod:`core.config`).
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .config import settings

try:  # SQLAlchemy is part of project requirements
    from sqlalchemy import (
        Column,
        MetaData,
        String,
        Table,
        Text,
        create_engine,
        delete,
        select,
        update,
        insert,
    )
except Exception:  # pragma: no cover - SQL backend not used/installed
    Column = MetaData = String = Table = Text = create_engine = None  # type: ignore
    delete = select = update = insert = None  # type: ignore


def _default_session() -> Dict[str, Any]:
    """Factory for an empty session context."""
    return {
        "history": [],
        "entities": {},
        "context_summaries": [],
        "vars": {},
        "sources": [],
        "full_document_text": None,
    }


class BaseContextStore(ABC):
    """Abstract interface for session context storage backends."""

    @abstractmethod
    def get(self, session_id: str) -> Dict[str, Any]:
        """Retrieve a session context, creating it if necessary."""

    @abstractmethod
    def save(self, session_id: str, data: Dict[str, Any]) -> None:
        """Persist the session context."""

    @abstractmethod
    def clear(self, session_id: str) -> None:
        """Remove a session context."""


class InMemoryContextStore(BaseContextStore):
    """Store context in memory using a simple dictionary."""

    def __init__(self) -> None:
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def get(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.sessions:
            self.sessions[session_id] = _default_session()
        return self.sessions[session_id]

    def save(self, session_id: str, data: Dict[str, Any]) -> None:
        self.sessions[session_id] = data

    def clear(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)


class SQLContextStore(BaseContextStore):
    """Store context in a SQL database using SQLAlchemy."""

    def __init__(self, url: str) -> None:
        if create_engine is None:  # pragma: no cover - missing dependency
            raise RuntimeError("SQLAlchemy is required for SQLContextStore")

        self.engine = create_engine(url, future=True)
        metadata = MetaData()
        self.table = Table(
            "context",
            metadata,
            Column("session_id", String, primary_key=True),
            Column("data", Text),
        )
        metadata.create_all(self.engine)

    def get(self, session_id: str) -> Dict[str, Any]:
        with self.engine.begin() as conn:
            row = conn.execute(
                select(self.table.c.data).where(self.table.c.session_id == session_id)
            ).fetchone()
            if row is None:
                session = _default_session()
                conn.execute(
                    insert(self.table).values(session_id=session_id, data=json.dumps(session))
                )
                return session
            return json.loads(row[0])

    def save(self, session_id: str, data: Dict[str, Any]) -> None:
        serialized = json.dumps(data)
        with self.engine.begin() as conn:
            exists = conn.execute(
                select(self.table.c.session_id).where(self.table.c.session_id == session_id)
            ).fetchone()
            if exists:
                conn.execute(
                    update(self.table)
                        .where(self.table.c.session_id == session_id)
                        .values(data=serialized)
                )
            else:
                conn.execute(
                    insert(self.table).values(session_id=session_id, data=serialized)
                )

    def clear(self, session_id: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(delete(self.table).where(self.table.c.session_id == session_id))


def _backend_from_settings() -> BaseContextStore:
    backend = getattr(settings, "CONTEXT_STORE_BACKEND", "memory").lower()
    if backend == "sql":
        url = getattr(settings, "CONTEXT_STORE_URL", "sqlite:///context.db")
        return SQLContextStore(url)
    return InMemoryContextStore()


class ContextManager:
    """High level API for manipulating session context."""

    def __init__(self, store: Optional[BaseContextStore] = None) -> None:
        self.store = store or _backend_from_settings()

    def get(self, session_id: str, question: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve or create a session context and optionally append question."""
        session = self.store.get(session_id)
        if question:
            session["history"].append(question)
            self.store.save(session_id, session)
        return session

    # --- Entities -----------------------------------------------------
    def set_entity(self, session_id: str, key: str, value: Any) -> None:
        ctx = self.get(session_id)
        ctx["entities"][key] = value
        self.store.save(session_id, ctx)

    def add_entities(self, session_id: str, entities: Dict[str, Any]) -> None:
        ctx = self.get(session_id)
        for k, v in entities.items():
            if k in ctx["entities"] and isinstance(ctx["entities"][k], list) and isinstance(v, list):
                ctx["entities"][k] = list(set(ctx["entities"][k] + v))
            else:
                ctx["entities"][k] = v
        self.store.save(session_id, ctx)

    def clear_entities(self, session_id: str) -> None:
        ctx = self.get(session_id)
        ctx["entities"] = {}
        self.store.save(session_id, ctx)

    # --- Context summaries --------------------------------------------
    def add_context_summary(self, session_id: str, summary: str) -> None:
        ctx = self.get(session_id)
        ctx["context_summaries"].append(summary)
        self.store.save(session_id, ctx)

    def get_context_summaries(self, session_id: str) -> List[str]:
        ctx = self.get(session_id)
        return ctx["context_summaries"]

    # --- Temporary variables ------------------------------------------
    def set_var(self, session_id: str, key: str, value: Any) -> None:
        ctx = self.get(session_id)
        ctx["vars"][key] = value
        self.store.save(session_id, ctx)

    def get_var(self, session_id: str, key: str, default=None):
        ctx = self.get(session_id)
        return ctx["vars"].get(key, default)

    # --- Sources ------------------------------------------------------
    def set_sources(self, session_id: str, sources: List[Dict[str, Any]]) -> None:
        ctx = self.get(session_id)
        ctx["sources"] = sources
        self.store.save(session_id, ctx)

    def get_sources(self, session_id: str) -> List[Dict[str, Any]]:
        ctx = self.get(session_id)
        return ctx.get("sources", [])

    def clear_sources(self, session_id: str) -> None:
        ctx = self.get(session_id)
        ctx["sources"] = []
        self.store.save(session_id, ctx)

    # --- Full document text ------------------------------------------
    def set_full_document_text(self, session_id: str, text: str) -> None:
        ctx = self.get(session_id)
        ctx["full_document_text"] = text
        self.store.save(session_id, ctx)

    def get_full_document_text(self, session_id: str) -> Optional[str]:
        ctx = self.get(session_id)
        return ctx.get("full_document_text")

    # --- Reset -------------------------------------------------------
    def clear(self, session_id: str) -> None:
        self.store.clear(session_id)

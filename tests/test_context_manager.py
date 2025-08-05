from core.context_manager import ContextManager


def test_context_manager_operations():
    cm = ContextManager()
    ctx = cm.get("s1", "q1")
    assert ctx["history"] == ["q1"]

    cm.set_entity("s1", "person", ["Alice"])
    cm.add_entities("s1", {"person": ["Bob"], "org": ["Acme"]})
    entities = cm.get("s1")["entities"]
    assert sorted(entities["person"]) == ["Alice", "Bob"]
    assert entities["org"] == ["Acme"]

    cm.clear_entities("s1")
    assert cm.get("s1")["entities"] == {}

    cm.add_context_summary("s1", "summary1")
    assert cm.get_context_summaries("s1") == ["summary1"]

    cm.set_var("s1", "flag", True)
    assert cm.get_var("s1", "flag") is True
    assert cm.get_var("s1", "missing", "def") == "def"

    sources = [{"text": "doc1"}]
    cm.set_sources("s1", sources)
    assert cm.get_sources("s1") == sources
    cm.clear_sources("s1")
    assert cm.get_sources("s1") == []

    cm.set_full_document_text("s1", "full text")
    assert cm.get_full_document_text("s1") == "full text"

    cm.clear("s1")
    assert "s1" not in cm.sessions

import types
import sys
import importlib
import asyncio


def _setup_agent(score):
    stub = types.ModuleType("pipelines.hybrid_retrieval")
    stub.hybrid_search = lambda query, top_k=7: [{"text": "doc", "rerank_score": score}]
    sys.modules["pipelines.hybrid_retrieval"] = stub
    import agents.agent_search as module
    importlib.reload(module)
    return module.SearchAgent()


def test_search_agent_success():
    agent = _setup_agent(2.0)
    ctx = {}
    assert agent.can_handle("trouve moi", ctx)
    result = asyncio.run(agent.run("question", ctx))
    assert result["sources"][0]["text"] == "doc"
    assert ctx["sources"]


def test_search_agent_low_confidence():
    agent = _setup_agent(0.5)
    ctx = {}
    result = asyncio.run(agent.run("question", ctx))
    assert result["sources"] == []
    assert ctx["sources"] == []
    assert "Aucun passage" in result["answer"]

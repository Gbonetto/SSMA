import types
import sys
import importlib
import asyncio


def test_synthesis_agent_run():
    stub = types.ModuleType("pipelines.rag_chain")
    stub.answer_with_rag = lambda question, top_k=5, user=None: {
        "answer": "resp",
        "sources": [{"text": "doc"}],
        "entities": {}
    }
    sys.modules["pipelines.rag_chain"] = stub
    import agents.agent_synthesis as module
    importlib.reload(module)
    agent = module.SynthesisAgent()
    ctx = {}
    assert agent.can_handle("any", ctx)
    result = asyncio.run(agent.run("question", ctx))
    assert result["answer"] == "resp"
    assert ctx["sources"] == [{"text": "doc"}]

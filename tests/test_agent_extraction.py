import types
import sys
import importlib
import asyncio


def test_extraction_agent_run():
    config_stub = types.ModuleType("core.config")
    config_stub.settings = types.SimpleNamespace(OPENAI_API_KEY="key")
    sys.modules["core.config"] = config_stub

    extract_stub = types.ModuleType("pipelines.extract_entities")
    extract_stub.extract_all_entities = lambda text, openai_api_key=None, fallback_llm=None, filter_result=True: {
        "PER": ["Alice"],
        "ORG": ["ACME"],
        "montants": ["100 €"],
        "dates": ["2023-01-01"],
    }
    sys.modules["pipelines.extract_entities"] = extract_stub

    hybrid_stub = types.ModuleType("pipelines.hybrid_retrieval")
    hybrid_stub.hybrid_search = lambda query, top_k=7: [{"text": "dummy", "rerank_score": 2.0}]
    sys.modules["pipelines.hybrid_retrieval"] = hybrid_stub

    import agents.agent_extraction as module
    importlib.reload(module)
    agent = module.ExtractionAgent()
    assert agent.can_handle("Quel est le montant?", {})
    context = {"sources": [{"text": "Alice a créé ACME le 2023-01-01 pour 100 €"}]}
    result = asyncio.run(agent.run("question", context))
    assert result["entities"]["PER"] == ["Alice"]
    assert result["entities"]["ORG"] == ["ACME"]
    assert "Alice" in result["answer"]

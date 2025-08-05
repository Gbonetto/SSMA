import asyncio
from agents.agent_n8n_webhook import N8NWebhookAgent


def test_n8n_webhook_agent():
    agent = N8NWebhookAgent()
    assert agent.can_handle("__n8n_webhook__", {})
    context = {
        "payload": {
            "entities": {"PER": ["Alice"]},
            "sources": [{"id": 1}],
            "actions": ["act"],
            "answer": "done",
            "extra": "x",
        }
    }
    result = asyncio.run(agent.run("__n8n_webhook__", context))
    assert result["status"] == "ok"
    assert result["entities"] == {"PER": ["Alice"]}
    assert result["actions"] == ["act"]
    assert result["result"] == "done"
    assert result["extra"] == {"extra": "x"}

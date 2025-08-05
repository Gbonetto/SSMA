import types
import sys
import importlib
import asyncio


def test_feedback_agent_ok():
    logging_stub = types.ModuleType("core.logging")
    called = {}

    def fake_log_feedback(answer_id, status, comment, user):
        called["args"] = (answer_id, status, comment, user)

    logging_stub.log_feedback = fake_log_feedback
    sys.modules["core.logging"] = logging_stub

    import agents.agent_feedback as module
    importlib.reload(module)
    agent = module.FeedbackAgent()
    assert agent.can_handle("feedback:123:utile:Bon", {})
    result = asyncio.run(agent.run("feedback:123:utile:Bon", {"user": "bob"}))
    assert called["args"] == ("123", "utile", "Bon", "bob")
    assert "123" in result["answer"]


def test_feedback_agent_bad_format():
    logging_stub = types.ModuleType("core.logging")
    logging_stub.log_feedback = lambda *a, **k: None
    sys.modules["core.logging"] = logging_stub
    import agents.agent_feedback as module
    importlib.reload(module)
    agent = module.FeedbackAgent()
    result = asyncio.run(agent.run("feedback:oops", {}))
    assert "Format de feedback incorrect" in result["answer"]

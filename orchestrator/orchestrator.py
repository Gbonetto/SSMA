import pkgutil
import importlib
import agents
from agents.base import Agent
from core.context_manager import ContextManager
from pipelines.rag_chain import detect_intention
from agents.agent_verifier import VerifierAgent

class Orchestrator:
    def __init__(self):
        self.context = ContextManager()
        self.agents: list[Agent] = self._ordered_agents()
        self.verifier = VerifierAgent()

    def _load_agents(self) -> list[Agent]:
        agents_list: list[Agent] = []
        for _, module_name, _ in pkgutil.iter_modules(agents.__path__):
            module = importlib.import_module(f"{agents.__name__}.{module_name}")
            for attr in dir(module):
                cls = getattr(module, attr)
                if isinstance(cls, type) and issubclass(cls, Agent) and cls is not Agent:
                    agents_list.append(cls())
        return agents_list

    def _ordered_agents(self) -> list[Agent]:
        all_agents = self._load_agents()
        def agent_priority(agent):
            cname = agent.__class__.__name__.lower()
            if "extraction" in cname:
                return 0
            if "search" in cname:
                return 1
            if "synthesis" in cname:
                return 2
            if "feedback" in cname:
                return 3
            if "n8n" in cname:
                return 4
            return 5
        return sorted(all_agents, key=agent_priority)

    async def handle(self, question: str, session_id: str = "default", context_override: dict = None) -> dict:
        sid = session_id or "default"
        if context_override is not None:
            ctx = context_override.copy()
        else:
            ctx = self.context.get(sid, question)

        intention = detect_intention(question)
        ctx["intention"] = intention

        # ---- FeedbackAgent (feedback:xxx)
        if question.lower().startswith("feedback:"):
            for agent in self.agents:
                if "feedback" in agent.__class__.__name__.lower():
                    if agent.can_handle(question, ctx):
                        return await agent.run(question, ctx)

        # ---- N8NWebhookAgent
        if question == "__n8n_webhook__" or ctx.get("n8n", False):
            for agent in self.agents:
                if "n8n" in agent.__class__.__name__.lower():
                    if agent.can_handle(question, ctx):
                        return await agent.run(question, ctx)

        # ---- Extraction prioritaire (intention ou mots-clÃ©s)
        entity_intents = ("entitÃ©", "montant", "date", "personne", "extrait", "extraire", "noms", "entreprise")
        if any(e in intention for e in entity_intents) or any(e in question.lower() for e in entity_intents):
            for agent in self.agents:
                if "extraction" in agent.__class__.__name__.lower():
                    try:
                        if agent.can_handle(question, ctx):
                            result = await agent.run(question, ctx)
                            if result and result.get("answer"):
                                ctx["last_answer"] = result.get("answer")
                                ctx["sources"] = result.get("sources", [])
                                return result
                    except Exception:
                        continue

        # ---- Recherche forcÃ©e (keywords, passages, etc.)
        if intention in ("recherche", "keyword", "passage"):
            ctx["force_search"] = True

        # ---- Boucle principale : le premier agent qui repond "gagne"
        for agent in self.agents:
            try:
                if agent.can_handle(question, ctx):
                    result = await agent.run(question, ctx)
                    if result and result.get("answer"):
                        ctx["last_answer"] = result.get("answer")
                        ctx["sources"] = result.get("sources", [])
                        if isinstance(agent, self._get_agent_class("SynthesisAgent")):
                            verification = await self.verifier.run(question, ctx)
                            result["auto_eval"] = verification.get("auto_eval")
                        return result
            except Exception:
                continue

        # ---- Fallback final
        return {
            "answer": "DÃ©solÃ©, je ne sais pas rÃ©pondre.",
            "sources": [],
            "entities": {}
        }

    def _get_agent_class(self, name):
        """Retourne la classe d'agent Ã  partir de son nom."""
        for agent in self.agents:
            if agent.__class__.__name__ == name:
                return agent.__class__
        return type(None)




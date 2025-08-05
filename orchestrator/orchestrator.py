import pkgutil
import importlib
import agents
from agents.base import Agent
from core.context_manager import ContextManager
from pipelines.rag_chain import detect_intention
from pipelines.auto_eval import auto_eval_llm  # <-- IMPORT AUTO-EVAL

class Orchestrator:
    def __init__(self):
        self.context = ContextManager()
        self.agents: list[Agent] = self._ordered_agents()

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

        # ---- PlannerAgent
        planner_cls = self._get_agent_class("PlannerAgent")
        planner_agent = None
        for ag in self.agents:
            if isinstance(ag, planner_cls):
                planner_agent = ag
                break
        agents_sequence = [ag for ag in self.agents if not isinstance(ag, planner_cls)]
        if planner_agent:
            plan_info = await planner_agent.run(question, ctx)
            ctx["plan"] = plan_info.get("plan", [])
            ctx.setdefault("reasoning", []).append(plan_info.get("reasoning", ""))
            ordered_names = plan_info.get("plan", [])
            agents_sequence = sorted(
                agents_sequence,
                key=lambda a: ordered_names.index(a.__class__.__name__)
                if a.__class__.__name__ in ordered_names else len(ordered_names)
            )
        else:
            ctx.setdefault("reasoning", [])

        # ---- FeedbackAgent (feedback:xxx)
        if question.lower().startswith("feedback:"):
            for agent in agents_sequence:
                if "feedback" in agent.__class__.__name__.lower():
                    if agent.can_handle(question, ctx):
                        result = await agent.run(question, ctx)
                        ctx["reasoning"].append(f"{agent.__class__.__name__} a fourni une réponse.")
                        return result

        # ---- N8NWebhookAgent
        if question == "__n8n_webhook__" or ctx.get("n8n", False):
            for agent in agents_sequence:
                if "n8n" in agent.__class__.__name__.lower():
                    if agent.can_handle(question, ctx):
                        result = await agent.run(question, ctx)
                        ctx["reasoning"].append(f"{agent.__class__.__name__} a fourni une réponse.")
                        return result

        # ---- Extraction prioritaire (intention ou mots-clés)
        entity_intents = ("entité", "montant", "date", "personne", "extrait", "extraire", "noms", "entreprise")
        if any(e in intention for e in entity_intents) or any(e in question.lower() for e in entity_intents):
            for agent in agents_sequence:
                if "extraction" in agent.__class__.__name__.lower():
                    try:
                        if agent.can_handle(question, ctx):
                            result = await agent.run(question, ctx)
                            if result and result.get("answer"):
                                ctx["last_answer"] = result.get("answer")
                                ctx["sources"] = result.get("sources", [])
                                ctx["reasoning"].append(f"{agent.__class__.__name__} a fourni une réponse.")
                                # --- AUTO-EVAL (hors agents infra)
                                if not isinstance(agent, (self._get_agent_class("FeedbackAgent"),
                                                          self._get_agent_class("N8NWebhookAgent"))):
                                    eval_result = auto_eval_llm(question, result["answer"], result.get("sources", []))
                                    result["auto_eval"] = eval_result
                                return result
                    except Exception:
                        continue

        # ---- Recherche forcée (keywords, passages, etc.)
        if intention in ("recherche", "keyword", "passage"):
            ctx["force_search"] = True

        # ---- Boucle principale : le premier agent qui répond “gagne”
        for agent in agents_sequence:
            try:
                if agent.can_handle(question, ctx):
                    result = await agent.run(question, ctx)
                    if result and result.get("answer"):
                        ctx["last_answer"] = result.get("answer")
                        ctx["sources"] = result.get("sources", [])
                        ctx["reasoning"].append(f"{agent.__class__.__name__} a fourni une réponse.")
                        # --- AUTO-EVAL (hors agents infra)
                        if not isinstance(agent, (self._get_agent_class("FeedbackAgent"),
                                                  self._get_agent_class("N8NWebhookAgent"))):
                            eval_result = auto_eval_llm(question, result["answer"], result.get("sources", []))
                            result["auto_eval"] = eval_result
                        return result
            except Exception:
                continue

        # ---- Fallback final
        ctx["reasoning"].append("Aucun agent n'a pu répondre, fallback activé.")
        return {
            "answer": "Désolé, je ne sais pas répondre.",
            "sources": [],
            "entities": {}
        }

    def _get_agent_class(self, name):
        """Retourne la classe d'agent Ã  partir de son nom."""
        for agent in self.agents:
            if agent.__class__.__name__ == name:
                return agent.__class__
        return type(None)



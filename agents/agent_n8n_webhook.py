from .base import Agent
import logging

class N8NWebhookAgent(Agent):
    def can_handle(self, question: str, context: dict) -> bool:
        # AppelÃ© par le endpoint /api/webhook/n8n ou via un flag dans le contexte
        return question == "__n8n_webhook__" or context.get("n8n", False)

    async def run(self, question: str, context: dict) -> dict:
        payload = context.get("payload", {})
        # Extraction robuste des champs attendus
        entities = payload.get("entities") or {}
        sources = payload.get("sources") or []
        actions = payload.get("actions") or []
        answer = payload.get("answer") or ""
        extra = {k: v for k, v in payload.items() if k not in ["entities", "sources", "actions", "answer"]}

        # Logging si besoin pour traÃ§abilitÃ© (optionnel)
        logging.info(f"[N8NWebhookAgent] Payload reÃ§u : entities={entities} | actions={actions} | extra={extra}")

        # PossibilitÃ© de traiter certaines actions ici, ou de simplement transmettre Ã  n8n
        return {
            "status": "ok",
            "answer": "DonnÃ©es transmises Ã  n8n.",
            "entities": entities,
            "sources": sources,
            "actions": actions,
            "result": answer,
            "extra": extra,  # Pour garder toutes les infos annexes Ã©ventuelles
            "raw": payload
        }




from fastapi import FastAPI, HTTPException, Request
from api.debug import router as debug_router
from api.admin import router as admin_router       # <--- ADMIN
from pydantic import BaseModel
from orchestrator.orchestrator import Orchestrator
from typing import Optional
from core.logging import log_endpoint
import json
import time

app = FastAPI(title="SMA-RAG Ultimate")
orch = Orchestrator()

# ---------- METRICS (middleware + endpoint) ----------
REQ_COUNT = 0
REQ_ERRORS = 0
TOTAL_TIME = 0.0

@app.middleware("http")
async def metrics_middleware(request, call_next):
    global REQ_COUNT, REQ_ERRORS, TOTAL_TIME
    start = time.time()
    try:
        response = await call_next(request)
        REQ_COUNT += 1
    except Exception:
        REQ_ERRORS += 1
        raise
    TOTAL_TIME += time.time() - start
    return response

@app.get("/metrics")
def get_metrics():
    return {
        "requests": REQ_COUNT,
        "errors": REQ_ERRORS,
        "avg_time_sec": (TOTAL_TIME / REQ_COUNT) if REQ_COUNT else 0
    }

# ---------- Standard Query ----------
class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = "default"

@app.post("/api/query")
@log_endpoint
async def query_endpoint(request: Request):
    try:
        body = await request.json()
        question = body.get("question")
        session_id = body.get("session_id", "default")
    except Exception as e:
        raw = await request.body()
        try:
            body = json.loads(raw.decode("utf-8"))
            question = body.get("question")
            session_id = body.get("session_id", "default")
        except Exception as e2:
            raise HTTPException(status_code=400, detail="Impossible de parser le body JSON envoyé.")

    if not question or not str(question).strip():
        raise HTTPException(status_code=422, detail="La question ne peut pas être vide")

    # ----- AUTO-EVAL -----
    result = await orch.handle(question, session_id)
    try:
        from pipelines.auto_eval import auto_eval_llm
        eval_result = auto_eval_llm(question, result.get("answer", ""), result.get("sources", []))
        result["auto_eval"] = eval_result
        from core.logging import log_auto_eval
        log_auto_eval(question, result.get("answer", ""), eval_result, session_id)
    except Exception as e:
        result["auto_eval"] = {"pertinence": -1, "clarte": -1, "commentaire": f"Auto-éval KO: {e}"}
    return result

# ---------- User Feedback ----------
class FeedbackRequest(BaseModel):
    answer_id: str
    status: str  # "utile", "inutile", etc.
    comment: Optional[str] = ""
    user: Optional[str] = "anonymous"

@app.post("/api/feedback")
@log_endpoint
async def feedback_endpoint(payload: FeedbackRequest):
    fake_question = f"feedback:{payload.answer_id}:{payload.status}:{payload.comment}"
    return await orch.handle(fake_question, payload.user or "feedback")

# ---------- Webhook n8n ----------
@app.post("/api/webhook/n8n")
@log_endpoint
async def n8n_webhook(request: Request):
    payload = await request.json()
    context_override = {"n8n": True, "payload": payload}
    return await orch.handle(
        question="__n8n_webhook__",
        session_id="n8n",
        context_override=context_override
    )

@app.get("/health")
@log_endpoint
def health():
    return {"status": "OK"}

# ---------- Admin & Debug ----------
app.include_router(debug_router)
app.include_router(admin_router)     # /admin/feedback et /admin/auto_eval





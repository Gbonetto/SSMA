from fastapi import FastAPI, HTTPException, Request
from api.debug import router as debug_router
from api.admin import router as admin_router       # <--- ADMIN
from pydantic import BaseModel
from orchestrator.orchestrator import Orchestrator
from typing import Optional
from core.logging import log_endpoint
import time
import asyncio
from pathlib import Path
from fastapi.responses import StreamingResponse, HTMLResponse
from core import event_stream

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
async def query_endpoint(payload: QueryRequest):
    if not payload.question or not str(payload.question).strip():
        raise HTTPException(status_code=422, detail="La question ne peut pas Ãªtre vide")

    session_id = payload.session_id or "default"

    # ----- AUTO-EVAL -----
    result = await orch.handle(payload.question, session_id)
    try:
        from pipelines.auto_eval import auto_eval_llm
        eval_result = auto_eval_llm(payload.question, result.get("answer", ""), result.get("sources", []))
        result["auto_eval"] = eval_result
        from core.logging import log_auto_eval
        log_auto_eval(payload.question, result.get("answer", ""), eval_result, session_id)
    except Exception as e:
        result["auto_eval"] = {"pertinence": -1, "clarte": -1, "commentaire": f"Auto-Ã©val KO: {e}"}
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


# ---------- Event streaming ----------

@app.get("/events")
async def events():
    queue = event_stream.register()

    async def event_generator():
        try:
            while True:
                data = await queue.get()
                yield f"data: {data}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            event_stream.unregister(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/live")
async def live_page():
    html_path = Path(__file__).with_name("live.html")
    return HTMLResponse(html_path.read_text(encoding="utf-8"))





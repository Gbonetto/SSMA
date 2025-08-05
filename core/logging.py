import os
import csv
from datetime import datetime
import logging
from functools import wraps

# --- CSV LOGGING CLASSIQUE ---

LOGS_DIR = os.path.join(os.path.dirname(__file__), "../logs")
os.makedirs(LOGS_DIR, exist_ok=True)
FEEDBACK_CSV = os.path.join(LOGS_DIR, "feedback.csv")
INTERACTIONS_CSV = os.path.join(LOGS_DIR, "interactions.csv")
REQUESTS_LOG = os.path.join(LOGS_DIR, "requests.log")  # AjoutÃ©

def log_auto_eval(question, answer, eval_result, session_id="default"):
    import os, csv
    from datetime import datetime
    LOGS_DIR = os.path.join(os.path.dirname(__file__), "../logs")
    os.makedirs(LOGS_DIR, exist_ok=True)
    AUTOEVAL_CSV = os.path.join(LOGS_DIR, "auto_eval.csv")
    now = datetime.now().isoformat()
    with open(AUTOEVAL_CSV, "a", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([now, session_id, question, answer, eval_result.get("pertinence"), eval_result.get("clarte"), eval_result.get("commentaire")])


def _ensure_csv_header(path, header):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, "w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)

def log_feedback(answer_id, status, comment, user=None):
    _ensure_csv_header(FEEDBACK_CSV, ["timestamp", "answer_id", "status", "comment", "user"])
    now = datetime.now().isoformat()
    with open(FEEDBACK_CSV, "a", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([now, answer_id, status, comment, user or "anonymous"])

def log_interaction(session_id, question, answer, agent, user=None, entities=None, sources=None):
    _ensure_csv_header(INTERACTIONS_CSV,
        ["timestamp", "session_id", "user", "question", "answer", "agent", "entities", "sources"]
    )
    now = datetime.now().isoformat()
    ent_str = str(entities) if entities else ""
    src_str = str(sources) if sources else ""
    with open(INTERACTIONS_CSV, "a", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            now, session_id, user or "anonymous", question, answer, agent, ent_str, src_str
        ])

# --- LOGGER API (requests.log) ---

api_logger = logging.getLogger("sma_api_logger")
api_logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
file_handler = logging.FileHandler(REQUESTS_LOG)
file_handler.setFormatter(formatter)
if not api_logger.handlers:
    api_logger.addHandler(file_handler)

def log_endpoint(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = datetime.now()
        req_name = func.__name__
        # Essayons d'extraire un payload pour le log (body ou request FastAPI)
        payload = {}
        try:
            # Pour POST body en pydantic
            if args and hasattr(args[0], "dict"):
                payload = args[0].dict()
            elif args:
                payload = str(args)
        except Exception:
            payload = str(args)
        # Optionnel : extraire l'IP si c'est un endpoint FastAPI avec Request en dernier arg
        client_ip = ""
        for arg in args:
            try:
                if hasattr(arg, "client"):
                    client_ip = getattr(arg.client, "host", "")
            except Exception:
                continue
        try:
            response = await func(*args, **kwargs)
            duration = (datetime.now() - start).total_seconds()
            api_logger.info(f"{req_name} | ip={client_ip} | payload={payload} | duration={duration:.3f}s | status=OK")
            return response
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            api_logger.error(f"{req_name} | ip={client_ip} | payload={payload} | duration={duration:.3f}s | ERROR={e}")
            raise
    return wrapper




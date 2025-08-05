from fastapi import APIRouter
import csv
import os

router = APIRouter()

@router.get("/admin/feedback")
def get_feedback():
    log_path = os.path.join(os.path.dirname(__file__), "../logs/feedback.csv")
    rows = []
    if os.path.exists(log_path):
        with open(log_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                rows.append(row)
    return {"feedback": rows}

@router.get("/admin/auto_eval")
def get_auto_eval():
    log_path = os.path.join(os.path.dirname(__file__), "../logs/auto_eval.csv")
    rows = []
    if os.path.exists(log_path):
        with open(log_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                rows.append(row)
    return {"auto_eval": rows}




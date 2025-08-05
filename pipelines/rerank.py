# pipelines/rerank.py
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np

# Télécharge le modèle au premier appel
class BGEReranker:
    def __init__(self, model_name="BAAI/bge-reranker-base"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)

    def rerank(self, query, passages, top_k=7):
        pairs = [(query, passage["text"]) for passage in passages]
        scores = []
        for q, p in pairs:
            inputs = self.tokenizer(q, p, truncation=True, padding=True, return_tensors="pt")
            with torch.no_grad():
                logits = self.model(**inputs).logits
            score = logits[0].item()
            scores.append(score)
        # Ajoute les scores au passage
        for i, passage in enumerate(passages):
            passage["rerank_score"] = scores[i]
        # Trie et garde top_k
        passages = sorted(passages, key=lambda x: -x["rerank_score"])
        return passages[:top_k]




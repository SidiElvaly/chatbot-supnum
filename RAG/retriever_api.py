from __future__ import annotations
import os
from typing import List
from fastapi import FastAPI, Query
from pydantic import BaseModel
import httpx

from .embedder import embed_texts
from .vector_store import load_index, search

app = FastAPI(title="SupNum RAG Retriever", version="1.1.0")

_index = None
_metadata = None

HF_TOKEN = os.getenv("HF_TOKEN", "")  # export HF_TOKEN="ton_token"
FR2AR_MODEL = "Helsinki-NLP/opus-mt-fr-ar"

def ensured_loaded():
    global _index, _metadata
    if _index is None or _metadata is None:
        _index, _metadata = load_index()

def contains_arabic(text: str) -> bool:
    return any("\u0600" <= ch <= "\u06FF" for ch in text)

def translate_fr_to_ar(text: str) -> str:
    if not HF_TOKEN:
        return text
    url = f"https://api-inference.huggingface.co/models/{FR2AR_MODEL}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": text, "options": {"wait_for_model": True}}
    try:
        r = httpx.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list) and data and "translation_text" in data[0]:
            return data[0]["translation_text"]
    except Exception:
        pass
    return text

class RetrieveTopItem(BaseModel):
    score: float
    question: str
    answer: str
    source: str
    tags: List[str]

class RetrieveResponse(BaseModel):
    query: str
    k: int
    result: RetrieveTopItem

@app.get("/retrieve", response_model=RetrieveResponse)
def retrieve(query: str = Query(..., min_length=1), k: int = 1):
    ensured_loaded()
    q_emb = embed_texts([query])
    hits = search(_index, q_emb[0], k=max(1, k))

    if not hits:
        return RetrieveResponse(query=query, k=k, result=RetrieveTopItem(score=0, question="", answer="", source="", tags=[]))

    best = max(hits, key=lambda h: h["score"])
    m = _metadata[best["idx"]]
    answer = m.get("answer", "")
    question = m.get("question", "")

    # Traduction vers arabe si la question est en arabe
    if contains_arabic(query) and not contains_arabic(answer):
        answer = translate_fr_to_ar(answer)
        question = translate_fr_to_ar(question)

    return RetrieveResponse(
        query=query,
        k=k,
        result=RetrieveTopItem(
            score=best["score"],
            question=question,
            answer=answer,
            source=m.get("source", ""),
            tags=m.get("tags", [])
        )
    )

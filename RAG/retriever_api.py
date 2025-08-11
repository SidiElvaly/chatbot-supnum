from __future__ import annotations
import os
from typing import List, Optional
from fastapi import FastAPI, Query
from pydantic import BaseModel

from .embedder import embed_texts
from .vector_store import load_index, hybrid_search

# --- réglages (peuvent aussi venir de params.yaml si tu veux) ---
CONFIDENCE_THRESHOLD = 0.35  # à tuner
ALPHA = 0.65                 # poids vectoriel dans la fusion

app = FastAPI(title="SupNum RAG Retriever", version="1.2.0")

_index = None
_metadata = None
_bm25 = None

def ensured_loaded():
    global _index, _metadata, _bm25
    if _index is None or _metadata is None or _bm25 is None:
        # INDEX_DIR optionnel (ex: export INDEX_DIR=./data/index)
        index_dir = os.getenv("INDEX_DIR", "./data/index")
        _index, _metadata, _bm25 = load_index(index_dir)

def _looks_arabic(text: str) -> bool:
    return any('\u0600' <= ch <= '\u06FF' for ch in text)

class RetrieveResponseItem(BaseModel):
    score: float
    question: str
    answer: str
    source: str
    tags: list
    needs_translation: bool = False

class RetrieveResponse(BaseModel):
    query: str
    k: int
    result: Optional[RetrieveResponseItem] = None
    low_confidence: bool = False

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/retrieve", response_model=RetrieveResponse)
def retrieve(query: str = Query(..., min_length=1), k: int = 1):
    ensured_loaded()
    q_is_ar = _looks_arabic(query)

    q_emb = embed_texts([query])[0]
    hits = hybrid_search(
        _index, _bm25, _metadata, q_emb, query_text=query,
        k_vec=8, k_bm25=8, top_final=max(k, 5), alpha=ALPHA
    )

    if not hits:
        return RetrieveResponse(query=query, k=1, result=None, low_confidence=True)

    # Top‑1 strict
    h = hits[0]
    m = _metadata[h["idx"]]
    ans = m.get("answer", "")

    needs_tr = False
    if q_is_ar and not _looks_arabic(ans):
        needs_tr = True

    low_conf = h["score"] < CONFIDENCE_THRESHOLD

    item = RetrieveResponseItem(
        score=h["score"],
        question=m.get("question", ""),
        answer=ans,
        source=m.get("source", ""),
        tags=m.get("tags", []),
        needs_translation=needs_tr
    )
    return RetrieveResponse(query=query, k=1, result=item, low_confidence=low_conf)

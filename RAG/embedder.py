# retriever/embedder.py
from __future__ import annotations
import os, time
from typing import List
import numpy as np
from huggingface_hub import InferenceClient
from httpx import HTTPStatusError

HF_MODEL = os.getenv("HF_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
HF_TOKEN = os.getenv("HF_TOKEN")

_client = InferenceClient(model=HF_MODEL, token=HF_TOKEN, timeout=60)

def _normalize(mat: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(mat, axis=1, keepdims=True) + 1e-12
    return mat / n

def _embed_one(text: str) -> np.ndarray:
    if len(text) > 5000:
        text = text[:5000]
    backoff = 1.0
    for _ in range(6):
        try:
            tok = _client.feature_extraction(text)  # supporté par les Sentence-Transformers
            arr = np.asarray(tok, dtype=np.float32)
            if arr.ndim == 2:
                vec = arr.mean(axis=0)
            elif arr.ndim == 1:
                vec = arr
            else:
                raise RuntimeError(f"Format inattendu: shape={arr.shape}")
            return vec.astype(np.float32)
        except HTTPStatusError as e:
            s = e.response.status_code
            if s in (409, 503, 529, 524):  # warm-up/surcharge → retry
                time.sleep(backoff); backoff = min(backoff*2, 8.0); continue
            if s == 401: raise RuntimeError("HF 401 Unauthorized: vérifie HF_TOKEN.")
            if s == 404: raise RuntimeError(f"HF 404 Not Found: modèle '{HF_MODEL}' introuvable.")
            if s == 400: raise RuntimeError(f"HF 400 Bad Request: {e.response.text}") from e
            raise
    raise RuntimeError("HF API indisponible après plusieurs retries.")

def embed_texts(texts: List[str]) -> np.ndarray:
    vecs = [_embed_one(t) for t in texts]
    return _normalize(np.stack(vecs, axis=0))

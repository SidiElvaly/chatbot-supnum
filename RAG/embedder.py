# retriever/embedder.py
from __future__ import annotations
import os
import json
import numpy as np
from huggingface_hub import InferenceClient

# ---- load params (optional) ----
_PARAMS = {}
try:
    import yaml  # make sure pyyaml is installed
    with open(os.path.join(os.path.dirname(__file__), "params.yaml"), "r", encoding="utf-8") as f:
        _PARAMS = yaml.safe_load(f) or {}
except Exception:
    _PARAMS = {}

# ---- Hugging Face Inference Client ----
_HF_TOKEN = os.getenv("HF_TOKEN") or (_PARAMS.get("huggingface", {}) or {}).get("token")
_MODEL_ID = (_PARAMS.get("huggingface", {}) or {}).get("model_id", "sentence-transformers/all-MiniLM-L6-v2")

_client = InferenceClient(model=_MODEL_ID, token=_HF_TOKEN)

def _mean_pooling(token_embeddings: list[list[float]]) -> np.ndarray:
    """
    token_embeddings: shape (seq_len, hidden) from HF Inference API
    returns: (hidden,)
    """
    arr = np.asarray(token_embeddings, dtype=np.float32)
    if arr.ndim != 2:
        # some providers may already return a single vector
        return arr.astype(np.float32)
    return arr.mean(axis=0).astype(np.float32)

def _l2_normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v if n == 0 else (v / n).astype(np.float32)

def _embed_one(text: str) -> np.ndarray:
    # For sentence-transformers, feature_extraction(text) returns token-level embeddings
    token_embs = _client.feature_extraction(text)
    vec = _mean_pooling(token_embs)
    return _l2_normalize(vec)

def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Returns (N, D) float32 L2-normalized embeddings
    """
    vecs = [_embed_one(t) for t in texts]
    return np.stack(vecs, axis=0).astype(np.float32)

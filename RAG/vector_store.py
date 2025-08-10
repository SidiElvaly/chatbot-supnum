from __future__ import annotations
import os, json
from typing import List, Dict, Any, Tuple
import numpy as np
import faiss

INDEX_DIR = os.getenv("INDEX_DIR", "./data/index")
EMB_DIM = int(os.getenv("EMB_DIM", "384"))  # all-MiniLM-L6-v2 = 384
METADATA_FILE = os.path.join(INDEX_DIR, "metadata.jsonl")
INDEX_FILE = os.path.join(INDEX_DIR, "faiss.index")
NPY_FILE = os.path.join(INDEX_DIR, "embeddings.npy")

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def save_index(embeddings: np.ndarray, metadata: List[Dict[str, Any]]):
    ensure_dir(INDEX_DIR)
    # Build FAISS index for cosine similarity using inner product on normalized vectors
    index = faiss.index_factory(embeddings.shape[1], "Flat", faiss.METRIC_INNER_PRODUCT)
    index.add(embeddings.astype("float32"))
    faiss.write_index(index, INDEX_FILE)
    np.save(NPY_FILE, embeddings.astype("float32"))
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        for m in metadata:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")

def load_index() -> Tuple[faiss.Index, List[Dict[str, Any]]]:
    if not (os.path.exists(INDEX_FILE) and os.path.exists(METADATA_FILE)):
        raise FileNotFoundError("Index or metadata not found. Run ingest.py first.")
    index = faiss.read_index(INDEX_FILE)
    metadata: List[Dict[str, Any]] = []
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                metadata.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return index, metadata

def search(index: faiss.Index, query_emb: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
    if query_emb.ndim == 1:
        query_emb = query_emb.reshape(1, -1)
    D, I = index.search(query_emb.astype("float32"), k)
    results = []
    for score, idx in zip(D[0].tolist(), I[0].tolist()):
        if idx == -1:
            continue
        results.append({"score": float(score), "idx": int(idx)})
    return results

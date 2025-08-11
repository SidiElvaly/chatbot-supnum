from __future__ import annotations
import os, json, pickle, re
from typing import List, Dict, Any
import numpy as np
import faiss
from rank_bm25 import BM25Okapi

# ---------- FAISS ----------
def save_index(index: faiss.IndexFlatIP, metadata: List[Dict[str, Any]], index_dir: str):
    os.makedirs(index_dir, exist_ok=True)
    faiss.write_index(index, os.path.join(index_dir, "faiss.index"))
    with open(os.path.join(index_dir, "meta.jsonl"), "w", encoding="utf-8") as f:
        for m in metadata:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")

def load_index(index_dir: str = None):
    index_dir = index_dir or os.getenv("INDEX_DIR", "./data/index")
    idx_path = os.path.join(index_dir, "faiss.index")
    meta_path = os.path.join(index_dir, "meta.jsonl")
    if not (os.path.exists(idx_path) and os.path.exists(meta_path)):
        raise FileNotFoundError("Index or metadata not found. Run ingest first.")
    index = faiss.read_index(idx_path)

    metadata = []
    with open(meta_path, "r", encoding="utf-8") as f:
        for line in f:
            metadata.append(json.loads(line))
    bm25, _ = load_bm25(index_dir)
    return index, metadata, bm25

def add_to_index(embs: np.ndarray) -> faiss.IndexFlatIP:
    dim = embs.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embs.astype(np.float32))
    return index

def search(index: faiss.IndexFlatIP, q_emb: np.ndarray, k: int = 5):
    q = q_emb.reshape(1, -1).astype(np.float32)
    scores, idxs = index.search(q, k)
    out = []
    for i, s in zip(idxs[0], scores[0]):
        if i == -1:
            continue
        out.append({"idx": int(i), "score": float(s)})
    return out

# ---------- BM25 ----------
def _tokenize(txt: str):
    # garde lettres/chiffres + arabe ; le reste -> espace
    txt = re.sub(r"[^\w\u0600-\u06FF]+", " ", txt, flags=re.UNICODE)
    return [t for t in txt.lower().split() if t]

def build_bm25(metadata: List[Dict[str, Any]]):
    corpus_tokens = []
    for m in metadata:
        doc_text = m.get("doc_text") or (m.get("question", "") + "\n" + m.get("answer", ""))
        corpus_tokens.append(_tokenize(doc_text))
    return BM25Okapi(corpus_tokens), corpus_tokens

def save_bm25(bm25: BM25Okapi, corpus_tokens: List[List[str]], index_dir: str):
    with open(os.path.join(index_dir, "bm25.pkl"), "wb") as f:
        pickle.dump({"bm25": bm25, "tokens": corpus_tokens}, f)

def load_bm25(index_dir: str):
    path = os.path.join(index_dir, "bm25.pkl")
    if not os.path.exists(path):
        return None, None
    with open(path, "rb") as f:
        obj = pickle.load(f)
    return obj["bm25"], obj["tokens"]

# ---------- Hybrid search ----------
def hybrid_search(index, bm25, metadata, q_emb, query_text,
                  k_vec=8, k_bm25=8, top_final=5, alpha=0.65):
    """
    alpha : poids du score vectoriel (0..1)
    """
    # 1) FAISS
    vec_hits = search(index, q_emb, k=k_vec)
    vec_scores = {h["idx"]: float(h["score"]) for h in vec_hits}

    # 2) BM25
    bm25_scores = {}
    if bm25 is not None:
        tokens = _tokenize(query_text)
        scores = bm25.get_scores(tokens)  # np.array(N)
        top_idx = np.argsort(scores)[::-1][:k_bm25]
        for i in top_idx:
            bm25_scores[int(i)] = float(scores[i])

    # 3) min-max normalisation par canal
    def _minmax(d):
        if not d: return {}
        vals = np.array(list(d.values()), dtype=np.float32)
        mn, mx = float(vals.min()), float(vals.max())
        if mx == mn:
            return {k: 0.0 for k in d}
        return {k: (v - mn) / (mx - mn) for k, v in d.items()}

    vec_n = _minmax(vec_scores)
    bm25_n = _minmax(bm25_scores)

    # 4) fusion
    fused = {}
    for i in set(list(vec_n.keys()) + list(bm25_n.keys())):
        fused[i] = alpha * vec_n.get(i, 0.0) + (1 - alpha) * bm25_n.get(i, 0.0)

    ranked = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:top_final]
    out = [{"idx": int(i), "score": float(s)} for i, s in ranked]
    return out

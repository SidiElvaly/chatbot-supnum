from __future__ import annotations
import argparse, os, json
import numpy as np

from embedder import embed_texts
from vector_store import add_to_index, save_index, build_bm25, save_bm25

def load_jsonl(path: str):
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line))
    return data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="JSONL avec {question, answer, source?, tags?}")
    parser.add_argument("--index_dir", default="./data/index")
    args = parser.parse_args()

    items = load_jsonl(args.data)

    # texte à embedder = question + réponse
    texts = []
    metadata = []
    for m in items:
        q = (m.get("question") or "").strip()
        a = (m.get("answer") or "").strip()
        doc_text = (q + "\n" + a).strip()
        texts.append(doc_text)

        meta = {
            "question": q,
            "answer": a,
            "source": m.get("source", ""),
            "tags": m.get("tags", []),
            "doc_text": doc_text,   # pour BM25
        }
        metadata.append(meta)

    embs = embed_texts(texts)  # (N, D) float32, L2-normalized
    index = add_to_index(embs)

    os.makedirs(args.index_dir, exist_ok=True)
    save_index(index, metadata, args.index_dir)

    bm25, toks = build_bm25(metadata)
    save_bm25(bm25, toks, args.index_dir)

    print(f"Indexed {len(items)} items into {args.index_dir}")

if __name__ == "__main__":
    main()

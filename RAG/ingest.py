from __future__ import annotations
import os, json, argparse
from typing import List, Dict, Any
import numpy as np
from embedder import embed_texts
from vector_store import save_index

def read_jsonl(path: str) -> List[Dict[str, Any]]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if "question" in obj and "answer" in obj:
                    rows.append({
                        "question": obj["question"],
                        "answer": obj["answer"],
                        "source": obj.get("source", os.path.basename(path)),
                        "tags": obj.get("tags", []),
                        "content": f"Q: {obj['question']}\nA: {obj['answer']}"
                    })
            except json.JSONDecodeError:
                continue
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="Path to JSONL with Q/A")
    ap.add_argument("--index_dir", default="./data/index", help="Where to write FAISS index")
    args = ap.parse_args()

    os.environ["INDEX_DIR"] = args.index_dir

    rows = read_jsonl(args.data)
    if not rows:
        raise SystemExit("No valid rows with question/answer found.")

    texts = [r["content"] for r in rows]
    embs = embed_texts(texts)  # normalized vectors
    if embs.ndim != 2:
        raise RuntimeError("Embeddings must be 2D")

    save_index(embs, rows)
    print(f"Indexed {len(rows)} items into {args.index_dir}")

if __name__ == "__main__":
    main()

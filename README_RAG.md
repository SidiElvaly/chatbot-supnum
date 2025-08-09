# RAG Retriever (FAISS + SentenceTransformers)

## Installation
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Ingestion (à partir du JSONL fusionné)
```bash
export INDEX_DIR=./data/index
python retriever/ingest.py --data /mnt/data/faq_supnum_merged.jsonl --index_dir $INDEX_DIR
```

## Lancer l'API
```bash
uvicorn retriever.retriever_api:app --reload --port 8001
```

## Tester
- Santé : http://localhost:8001/health
- Recherche : http://localhost:8001/retrieve?query=Quels%20sont%20les%20modules%20du%20semestre%201&k=5

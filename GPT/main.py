
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import os
import requests
from openai import OpenAI
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("La clé OPENAI_API_KEY doit être définie dans le fichier .env")

client = OpenAI(api_key=OPENAI_API_KEY)

# URL de ton API /retrieve distante
RETRIEVE_API_URL = os.getenv("RETRIEVE_API_URL", "http://localhost:8001/retrieve")

# Charger le prompt de base
with open("GPT/prompts/default.txt", "r", encoding="utf-8") as f:
    base_prompt = f.read().strip()


def get_relevant_context(question: str, k: int = 3) -> str:
    """Appelle l'API /retrieve distante pour récupérer le contexte"""
    try:
        response = requests.get(
            RETRIEVE_API_URL,
            params={"query": question, "k": k},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        # On suppose que l'API retourne un tableau d'objets { "question": "...", "answer": "..." }
        contexts = [
            f"Q: {item.get('question', '')}\nA: {item.get('answer', '')}"
            for item in data.get("results", [])
        ]
        return "\n\n".join(contexts)
    except Exception as e:
        raise RuntimeError(f"Erreur lors de l'appel à l'API /retrieve : {e}")


@app.get("/chat")
async def chat(
    question: str = Query(..., description="Question de l'utilisateur"),
    lang: str = Query("fr", description="Langue de la question (fr, en, ar...)")
):
    try:
        # Traduction si besoin
        question_fr = question if lang == "fr" else GoogleTranslator(source='auto', target='fr').translate(question)

        # Récupération du contexte depuis l'API externe
        context = get_relevant_context(question_fr, k=3)

        # Préparation du prompt
        messages = [
            {"role": "system", "content": base_prompt},
            {"role": "user", "content": f"Contexte :\n{context}\n\nQuestion : {question_fr}"}
        ]

        # Appel à GPT
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )
        answer_fr = response.choices[0].message.content

        # Traduction si nécessaire
        answer = answer_fr if lang == "fr" else GoogleTranslator(source='fr', target=lang).translate(answer_fr)

        return JSONResponse(content={"question": question, "answer": answer, "lang": lang})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)



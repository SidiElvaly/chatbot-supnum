
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
    import requests

    try:
        url = f"http://localhost:8001/retrieve?query={question}&k={k}"

        response = requests.get(url)

        if response.status_code != 200:
            print("[ERREUR] Échec de la requête /retrieve")
            return ""

        results = response.json()

        # Extraire le contexte pertinent depuis la clé "result"
        result = results.get("result", {})
        if not result:
            print("[INFO] Aucun résultat trouvé par /retrieve.")
            return ""

        # Construire un contexte à partir de la question et la réponse trouvées
        question_trouvee = result.get("question", "")
        reponse = result.get("answer", "")

        context = f"Question trouvée : {question_trouvee}\nRéponse : {reponse}"

        print(f"[DEBUG] Contexte extrait: {context}")

        return context.strip()

    except Exception as e:
        print(f"[ERREUR] Exception dans get_relevant_context: {e}")
        return ""

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
        # print(context)

        # Préparation du prompt
        messages = [
             {
                "role": "system",
                "content": base_prompt
            },
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

# Chat API (Client GPT + API /retrieve distante)

## Installation
```bash
python -m venv venv && venv\Scripts\activate     # Sur Windows
# ou
python -m venv venv && source venv/bin/activate  # Sur Linux/Mac

pip install -r requirements.txt

```

## Configuration
- Créer un fichier .env à la racine du projet avec :
OPENAI_API_KEY=

## Lancer l'API
```bash
uvicorn GPT.main:app --reload --port 8002
```

## Tester
- Exemple (Français) : http://localhost:8002/chat?question=Quels%20sont%20les%20modules%20du%20semestre%201
- Exemple (Anglais) : http://localhost:8002/chat?question=What%20are%20the%20modules%20of%20semester%201&lang=en
- Exemple (Arabe) : http://localhost:8002/chat?question=ما%20هي%20مقررات%20الفصل%20الأول؟&lang=ar



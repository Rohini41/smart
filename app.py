import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types

from chatbot_config import SYSTEM_PROMPT, MODEL_NAME

load_dotenv()

app = Flask(__name__)

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

OFF_TOPIC_REPLY = (
    "I’m the Smart City AI study assistant. I can only answer educational "
    "questions related to smart cities, urban technology, sustainability, "
    "IoT, intelligent transportation, smart infrastructure, and related topics."
)


def looks_relevant(message: str) -> bool:
    keywords = {
        "smart city", "smart cities", "urban", "city", "cities",
        "iot", "internet of things", "sensor", "sensors",
        "traffic", "transport", "transportation", "mobility",
        "smart grid", "energy", "renewable", "sustainability",
        "waste", "water", "pollution", "air quality",
        "infrastructure", "governance", "e-governance",
        "parking", "street light", "streetlight", "public safety",
        "digital twin", "5g", "ai", "artificial intelligence",
        "machine learning", "data", "cloud", "cybersecurity",
        "education", "study", "project", "assignment", "exam"
    }
    text = message.lower()
    return any(keyword in text for keyword in keywords)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({"error": "Please enter a question."}), 400

    if len(message) > 4000:
        return jsonify({"error": "Please keep your question under 4000 characters."}), 400

    if not looks_relevant(message):
        return jsonify({"reply": OFF_TOPIC_REPLY})

    if client is None:
        return jsonify({"error": "Gemini API key is not configured."}), 500

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=1200,
            ),
        )

        reply = response.text.strip() if response.text else (
            "I could not generate an answer right now. Please try again."
        )
        return jsonify({"reply": reply})

    except Exception:
        return jsonify({
            "error": "The AI service is temporarily unavailable. Please try again."
        }), 502


if __name__ == "__main__":
    app.run()

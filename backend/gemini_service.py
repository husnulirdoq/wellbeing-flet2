import requests
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent"

SYSTEM_PROMPT = """You are a compassionate AI health and wellness assistant for the WellBeing Tracker app.
Your role is to:
- Provide personalized wellness advice based on user's mood, sleep, exercise, and stress data
- Give practical tips for improving mental and physical health
- Be empathetic, supportive, and encouraging
- Keep responses concise (2-3 sentences max) and actionable
- Respond in the same language the user uses (Indonesian or English)
"""

def chat(message: str, history: list = None) -> str:
    if not GEMINI_API_KEY:
        return "Gemini API key not configured."

    contents = []

    # Add history
    if history:
        for h in history[-6:]:  # last 6 messages for context
            contents.append({
                "role": h["role"],
                "parts": [{"text": h["text"]}]
            })

    # Add current message
    contents.append({
        "role": "user",
        "parts": [{"text": message}]
    })

    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 256,
        }
    }

    try:
        resp = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json=payload,
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        elif resp.status_code == 429:
            import time
            time.sleep(5)
            resp = requests.post(
                f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                json=payload,
                timeout=15,
            )
            if resp.status_code == 200:
                return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            return "Quota AI hari ini sudah habis. Coba lagi besok atau aktifkan billing di Google AI Studio."
        return f"Error: {resp.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

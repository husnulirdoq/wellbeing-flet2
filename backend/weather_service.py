import requests
import os

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

def get_weather(city: str = "Jakarta") -> dict:
    if not WEATHER_API_KEY:
        return {"error": "Weather API key not configured"}
    try:
        resp = requests.get(WEATHER_URL, params={
            "q": city,
            "appid": WEATHER_API_KEY,
            "units": "metric",
            "lang": "id",
        }, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "city":        data["name"],
                "temp":        round(data["main"]["temp"]),
                "feels_like":  round(data["main"]["feels_like"]),
                "humidity":    data["main"]["humidity"],
                "description": data["weather"][0]["description"],
                "icon":        data["weather"][0]["icon"],
                "wind_speed":  data["wind"]["speed"],
            }
        return {"error": f"City not found: {city}"}
    except Exception as e:
        return {"error": str(e)}

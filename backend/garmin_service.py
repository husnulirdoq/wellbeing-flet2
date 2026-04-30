import os
from datetime import date

GARMIN_EMAIL    = os.getenv("GARMIN_EMAIL", "")
GARMIN_PASSWORD = os.getenv("GARMIN_PASSWORD", "")

_client = None

def get_client():
    global _client
    if _client is not None:
        return _client
    try:
        from garminconnect import Garmin
        client = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
        client.login()
        _client = client
        return _client
    except Exception as e:
        raise Exception(f"Garmin login failed: {e}")

def get_today_stats(target_date: str = None) -> dict:
    if not GARMIN_EMAIL or not GARMIN_PASSWORD:
        return {"error": "Garmin credentials not configured", "source": "garmin"}
    try:
        client = get_client()
        d = target_date or str(date.today())

        stats = client.get_stats(d)
        sleep = client.get_sleep_data(d)
        hr    = client.get_heart_rates(d)

        # Sleep
        sleep_seconds = sleep.get("dailySleepDTO", {}).get("sleepTimeSeconds", 0)
        sleep_hours   = round(sleep_seconds / 3600, 1)

        # Heart rate
        resting_hr = stats.get("restingHeartRate", 0) or hr.get("restingHeartRate", 0)

        # Steps & exercise
        steps            = stats.get("totalSteps", 0)
        exercise_minutes = stats.get("moderateIntensityMinutes", 0) + \
                           stats.get("vigorousIntensityMinutes", 0) * 2

        return {
            "sleep":      sleep_hours,
            "exercise":   exercise_minutes or round(steps / 100),
            "water":      0,
            "heart_rate": resting_hr,
            "meditation": 0,
            "steps":      steps,
            "source":     "garmin",
        }
    except Exception as e:
        global _client
        _client = None  # reset on error
        return {"error": str(e), "source": "garmin"}

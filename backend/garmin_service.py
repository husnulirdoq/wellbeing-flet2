from datetime import date
import os

GARMIN_EMAIL    = os.getenv("GARMIN_EMAIL", "")
GARMIN_PASSWORD = os.getenv("GARMIN_PASSWORD", "")

try:
    from garminconnect import Garmin
    GARMIN_AVAILABLE = True
except ImportError:
    GARMIN_AVAILABLE = False

_client = None

def get_client():
    global _client
    if not GARMIN_AVAILABLE:
        return None
    if _client is None:
        from garminconnect import Garmin
        _client = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
        _client.login()
    return _client

def get_today_stats(target_date: str = None) -> dict:
    """Fetch today's stats from Garmin Connect."""
    if not GARMIN_AVAILABLE:
        return {"error": "Garmin not available on this server", "source": "garmin"}
    if not GARMIN_EMAIL or not GARMIN_PASSWORD:
        return {"error": "Garmin credentials not configured", "source": "garmin"}
    d = target_date or str(date.today())
    try:
        client = get_client()
        stats        = client.get_stats(d)
        sleep        = client.get_sleep_data(d)
        heart_rates  = client.get_heart_rates(d)
        stress       = client.get_stress_data(d)

        # Sleep hours
        sleep_seconds = sleep.get("dailySleepDTO", {}).get("sleepTimeSeconds", 0)
        sleep_hours   = round(sleep_seconds / 3600, 1)

        # Resting heart rate
        resting_hr = stats.get("restingHeartRate", 0)

        # Average stress (0-100)
        avg_stress = stress.get("avgStressLevel", 0)

        # Steps → convert to exercise minutes (rough estimate: 100 steps/min)
        steps = stats.get("totalSteps", 0)
        exercise_minutes = round(steps / 100)

        return {
            "sleep":      sleep_hours,
            "exercise":   exercise_minutes,
            "water":      0,          # Garmin doesn't track water by default
            "heart_rate": resting_hr,
            "meditation": 0,          # not available from Garmin
            "steps":      steps,
            "avg_stress": avg_stress,
            "source":     "garmin",
        }
    except Exception as e:
        return {"error": str(e), "source": "garmin"}

import requests
import os

FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "")
FIREBASE_VERIFY_URL = "https://identitytoolkit.googleapis.com/v1/accounts:lookup"

def verify_firebase_token(id_token: str) -> dict:
    """Verify Firebase ID token and return user info."""
    resp = requests.post(
        f"{FIREBASE_VERIFY_URL}?key={FIREBASE_API_KEY}",
        json={"idToken": id_token},
        timeout=10,
    )
    if resp.status_code != 200:
        return None
    users = resp.json().get("users", [])
    return users[0] if users else None

import os
import uuid
import hashlib
import hmac as hmac_module
import base64
import json
import requests
from datetime import datetime, timezone

DOKU_API_KEY        = os.getenv("DOKU_API_KEY", "")
DOKU_SECRET_KEY     = os.getenv("DOKU_SECRET_KEY", "")  # Active Secret Key (RSA Private Key)
DOKU_IS_SANDBOX     = os.getenv("DOKU_IS_SANDBOX", "true").lower() == "true"

BASE_URL = "https://api-sandbox.doku.com" if DOKU_IS_SANDBOX else "https://api.doku.com"

def generate_asymmetric_signature(string_to_sign: str, private_key_str: str) -> str:
    """Generate HMAC-SHA256 signature (DOKU non-SNAP)."""
    sig = hmac_module.new(
        private_key_str.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha256
    )
    return base64.b64encode(sig.digest()).decode("utf-8")

def create_transaction(order_items: list, customer: dict, total: float) -> dict:
    if not DOKU_API_KEY or not DOKU_SECRET_KEY:
        return {"error": "DOKU credentials not configured"}

    order_id      = f"WELLBEING-{uuid.uuid4().hex[:8].upper()}"
    external_id   = str(uuid.uuid4())
    timestamp     = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    amount_idr    = int(total * 15500)
    target        = "/checkout/v1/payment"

    body = {
        "order": {
            "invoice_number": order_id,
            "amount":         amount_idr,
            "currency":       "IDR",
            "callback_url":   "https://wellbeing.app/payment/callback",
            "auto_redirect":  True,
            "line_items": [
                {
                    "name":     item["name"][:50],
                    "price":    int(item["price"] * 15500),
                    "quantity": item.get("quantity", 1),
                }
                for item in order_items
            ],
        },
        "payment": {
            "payment_due_date": 60,
        },
        "customer": {
            "name":  customer.get("name", "User")[:30],
            "email": customer.get("email", "user@example.com"),
        },
    }

    body_str = json.dumps(body, separators=(",", ":"))

    # Generate digest
    digest = base64.b64encode(
        hashlib.sha256(body_str.encode("utf-8")).digest()
    ).decode("utf-8")

    # String to sign for asymmetric
    string_to_sign = f"Client-Id:{DOKU_API_KEY}\nRequest-Id:{external_id}\nRequest-Timestamp:{timestamp}\nRequest-Target:{target}\nDigest:{digest}"

    try:
        signature = generate_asymmetric_signature(string_to_sign, DOKU_SECRET_KEY)
        sig_header = f"HMACSHA256={signature}"
    except Exception as e:
        return {"error": str(e)}

    headers = {
        "Client-Id":         DOKU_API_KEY,
        "Request-Id":        external_id,
        "Request-Timestamp": timestamp,
        "Signature":         sig_header,
        "Content-Type":      "application/json",
    }

    try:
        resp = requests.post(f"{BASE_URL}{target}", data=body_str, headers=headers, timeout=15)
        data = resp.json()
        if resp.status_code == 200:
            payment_url = data.get("response", {}).get("payment", {}).get("url", "") or \
                          data.get("payment", {}).get("url", "")
            return {
                "order_id":    order_id,
                "payment_url": payment_url,
            }
        return {"error": f"DOKU {resp.status_code}: {json.dumps(data)[:300]}"}
    except Exception as e:
        return {"error": str(e)}

def verify_notification(notification_data: dict) -> dict:
    return {"status": notification_data.get("transaction", {}).get("status", "unknown")}

import os
import uuid
import json
import requests
import base64

MIDTRANS_SERVER_KEY    = os.getenv("MIDTRANS_SERVER_KEY", "")
MIDTRANS_IS_PRODUCTION = os.getenv("MIDTRANS_IS_PRODUCTION", "false").lower() == "true"

BASE_URL = "https://app.midtrans.com" if MIDTRANS_IS_PRODUCTION else "https://app.sandbox.midtrans.com"

def get_headers():
    encoded = base64.b64encode(f"{MIDTRANS_SERVER_KEY}:".encode()).decode()
    return {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

def create_transaction(order_items: list, customer: dict, total: float) -> dict:
    if not MIDTRANS_SERVER_KEY:
        return {"error": "Midtrans not configured"}

    order_id   = f"WELLBEING-{uuid.uuid4().hex[:8].upper()}"
    amount_idr = int(total * 15500)

    payload = {
        "transaction_details": {
            "order_id":     order_id,
            "gross_amount": amount_idr,
        },
        "item_details": [
            {
                "id":       str(idx),
                "price":    int(item["price"] * 15500),
                "quantity": item.get("quantity", 1),
                "name":     item["name"][:50],
            }
            for idx, item in enumerate(order_items)
        ],
        "customer_details": {
            "first_name": customer.get("name", "User")[:30],
            "email":      customer.get("email", "user@example.com"),
        },
        "callbacks": {
            "finish": "https://wellbeing.app/payment/finish",
        },
    }

    try:
        resp = requests.post(
            f"{BASE_URL}/snap/v1/transactions",
            headers=get_headers(),
            json=payload,
            timeout=15,
        )
        data = resp.json()
        if resp.status_code in (200, 201):
            return {
                "order_id":     order_id,
                "snap_token":   data.get("token"),
                "payment_url":  data.get("redirect_url"),
            }
        return {"error": f"Midtrans {resp.status_code}: {data.get('error_messages', data)}"}
    except Exception as e:
        return {"error": str(e)}

def verify_notification(notification_data: dict) -> dict:
    return {"status": notification_data.get("transaction_status", "unknown")}

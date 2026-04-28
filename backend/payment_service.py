import midtransclient
import os
import uuid

MIDTRANS_SERVER_KEY = os.getenv("MIDTRANS_SERVER_KEY", "")
MIDTRANS_IS_PRODUCTION = os.getenv("MIDTRANS_IS_PRODUCTION", "false").lower() == "true"

def get_snap_client():
    return midtransclient.Snap(
        is_production=MIDTRANS_IS_PRODUCTION,
        server_key=MIDTRANS_SERVER_KEY,
    )

def create_transaction(order_items: list, customer: dict, total: float) -> dict:
    """
    Create a Midtrans Snap transaction.
    Returns snap_token and redirect_url.
    """
    snap = get_snap_client()
    order_id = f"WELLBEING-{uuid.uuid4().hex[:8].upper()}"

    param = {
        "transaction_details": {
            "order_id":     order_id,
            "gross_amount": int(total * 15000),  # USD to IDR rough conversion
        },
        "item_details": [
            {
                "id":       str(i),
                "price":    int(item["price"] * 15000),
                "quantity": item.get("quantity", 1),
                "name":     item["name"][:50],
            }
            for i, item in enumerate(order_items)
        ],
        "customer_details": {
            "first_name": customer.get("name", "User"),
            "email":      customer.get("email", "user@example.com"),
        },
    }

    transaction = snap.create_transaction(param)
    return {
        "order_id":     order_id,
        "snap_token":   transaction.get("token"),
        "redirect_url": transaction.get("redirect_url"),
    }

def verify_notification(notification_data: dict) -> dict:
    """Verify Midtrans payment notification."""
    core = midtransclient.CoreApi(
        is_production=MIDTRANS_IS_PRODUCTION,
        server_key=MIDTRANS_SERVER_KEY,
    )
    status = core.transactions.notification(notification_data)
    return status

TOPIC = "payment-events"

PAYMENT_TYPES = ["card", "crypto", "bank", "wallet"]


def key_for(payment_type: str) -> str:
    if payment_type not in PAYMENT_TYPES:
        raise ValueError(f"Unknown payment type: {payment_type}")
    return payment_type
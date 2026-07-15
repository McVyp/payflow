import json
import random
import time
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .kafka_client import get_producer, get_cluster_state
from .topics import TOPIC, PAYMENT_TYPES, key_for

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

producer = get_producer()

AMOUNT_RANGES = {
    "card": (5, 500),
    "crypto": (10, 5000),
    "bank": (50, 10000),
    "wallet": (1, 200),
}


class ClickRequest(BaseModel):
    paymentType: str


def random_amount(payment_type: str) -> float:
    low, high = AMOUNT_RANGES.get(payment_type, (1, 100))
    return round(low + random.random() * (high - low), 2)


@app.post("/api/click")
def click(req: ClickRequest):
    if req.paymentType not in PAYMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"paymentType must be one of {', '.join(PAYMENT_TYPES)}",
        )

    event = {
        "eventId": str(uuid.uuid4()),
        "paymentType": req.paymentType,
        "amount": random_amount(req.paymentType),
        "status": "processed",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "sentAtMs": int(time.time() * 1000),
    }

    try:
        producer.produce(
            topic=TOPIC,
            key=key_for(req.paymentType),
            value=json.dumps(event),
        )
        producer.flush(timeout=5)
    except Exception as err:
        print(f"Failed to publish event: {err}")
        raise HTTPException(status_code=500, detail="Failed to publish event")

    return {"ok": True, "event": event}


@app.get("/api/cluster")
def cluster():
    try:
        return get_cluster_state()
    except Exception as err:
        print(f"Failed to fetch cluster state: {err}")
        raise HTTPException(status_code=500, detail="Failed to fetch cluster state")


@app.get("/health")
def health():
    return {"ok": True}
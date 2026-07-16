import asyncio
import json
import threading
from queue import Queue, Empty

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .kafka_client import seek_back, subscribe, poll_message, commit_offset, get_group_state
from .db import insert_transaction, get_history, reset_history, get_stats

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

sse_queues: list[Queue] = []
sse_lock = threading.Lock()


def broadcast(payload: dict):
    data = json.dumps(payload)
    with sse_lock:
        for q in sse_queues:
            q.put(data)


def consumer_loop():
    subscribe()
    while True:
        result = poll_message(timeout=1.0)
        if result is None:
            continue

        event = result["event"]
        try:
            row = insert_transaction(
                event_id=event["eventId"],
                payment_type=event["paymentType"],
                amount=event["amount"],
                status=event["status"],
                partition=result["partition"],
                offset=result["offset"],
            )
            if row:
                row["created_at"] = row["created_at"].isoformat()
                row["amount"] = float(row["amount"])
                broadcast({
                    "type": "transaction",
                    "partition": result["partition"],
                    "row": row,
                    "sentAtMs": event.get("sentAtMs"),
                })
            commit_offset(result["_raw"])
        except Exception as err:
            print(f"Failed to process message: {err}")
            seek_back(result["_raw"])

@app.on_event("startup")
def startup():
    thread = threading.Thread(target=consumer_loop, daemon=True)
    thread.start()


@app.get("/api/stream")
async def stream():
    q: Queue = Queue()
    with sse_lock:
        sse_queues.append(q)

    async def event_generator():
        try:
            while True:
                try:
                    data = q.get_nowait()
                    yield f"data: {data}\n\n"
                except Empty:
                    await asyncio.sleep(0.2)
        finally:
            with sse_lock:
                sse_queues.remove(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/history")
def history():
    return get_history(50)


@app.post("/api/reset")
def reset():
    reset_history()
    broadcast({"type": "reset"})
    return {"ok": True}


@app.get("/api/group")
def group():
    return get_group_state()


@app.get("/api/stats")
def stats():
    return get_stats()


@app.get("/health")
def health():
    return {"ok": True}
import os
import json
import threading
import time
from confluent_kafka import Consumer, TopicPartition
from confluent_kafka.admin import AdminClient

BROKERS = os.environ.get("KAFKA_BROKERS", "localhost:9092")
TOPIC = "payment-events"
GROUP_ID = "payments-consumer-group"

_consumer = Consumer({
    "bootstrap.servers": BROKERS,
    "group.id": GROUP_ID,
    "auto.offset.reset": "latest",
    "enable.auto.commit": False,
})
_admin = AdminClient({"bootstrap.servers": BROKERS})


def get_consumer() -> Consumer:
    return _consumer


def subscribe():
    _consumer.subscribe([TOPIC])


_consumer_lock = threading.Lock()


def poll_message(timeout=1.0):
    with _consumer_lock:
        msg = _consumer.poll(timeout)
    if msg is None or msg.error():
        return None
    event = json.loads(msg.value().decode("utf-8"))
    return {"partition": msg.partition(), "offset": msg.offset(), "event": event, "_raw": msg}


def commit_offset(msg):
    with _consumer_lock:
        _consumer.commit(message=msg, asynchronous=False)

def seek_back(msg):
    with _consumer_lock:
        tp = TopicPartition(msg.topic(), msg.partition(), msg.offset())
        _consumer.seek(tp)

def get_group_state() -> dict:
    last_err = None
    for _ in range(3):
        try:
            desc_futures = _admin.describe_consumer_groups([GROUP_ID])
            group_desc = desc_futures[GROUP_ID].result()
            break
        except Exception as err:
            last_err = err
            time.sleep(1)
    else:
        raise last_err

    members = [
        {"memberId": m.member_id, "clientId": m.client_id, "clientHost": m.host}
        for m in group_desc.members
    ]

    metadata = _admin.list_topics(topic=TOPIC, timeout=10)
    topic_meta = metadata.topics.get(TOPIC)
    partition_ids = sorted(topic_meta.partitions.keys()) if topic_meta else []

    tps = [TopicPartition(TOPIC, pid) for pid in partition_ids]

    lag_by_partition = []
    with _consumer_lock:
        committed = None
        for _ in range(3):
            try:
                committed = _consumer.committed(tps, timeout=10)
                break
            except Exception:
                time.sleep(1)
        if committed is None:
            committed = []

        for tp in committed:
            _, high = _consumer.get_watermark_offsets(tp, timeout=10, cached=False)
            committed_offset = tp.offset if tp.offset is not None and tp.offset >= 0 else 0
            lag = max(high - committed_offset, 0)
            lag_by_partition.append({
                "partition": tp.partition,
                "committedOffset": committed_offset,
                "highWatermark": high,
                "lag": lag,
            })

    return {
        "groupId": GROUP_ID,
        "state": str(group_desc.state),
        "protocol": getattr(group_desc, "partition_assignor", ""),
        "members": members,
        "lagByPartition": lag_by_partition,
    }
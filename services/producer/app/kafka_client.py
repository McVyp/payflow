import os
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient
from .topics import TOPIC

BROKERS = os.environ.get("KAFKA_BROKERS", "localhost:9092")

_producer = Producer({"bootstrap.servers": BROKERS})
_admin = AdminClient({"bootstrap.servers": BROKERS})

def get_producer() -> Producer:
    return _producer

def get_cluster_state() -> dict:
    metadata = _admin.list_topics(topic=TOPIC, timeout=10)
    brokers = [
        {"nodeId": b.id, "host": b.host, "port": b.port}
        for b in metadata.brokers.values()
    ]

    topic_meta = metadata.topics.get(TOPIC)
    partitions = []
    if topic_meta is not None:
        for pid, p in topic_meta.partitions.items():
            partitions.append(
                {
                    "partitionId": pid,
                    "leader": p.leader,
                    "replicas": list(p.replicas),
                    "isr": list(p.isrs),
                }
            )
        partitions.sort(key=lambda p: p["partitionId"])

    return {
        "brokers": brokers,
        "controller": metadata.controller_id,
        "clusterId": getattr(metadata, "cluster_id", None),
        "topic": {"name": TOPIC, "partitions": partitions},
    }

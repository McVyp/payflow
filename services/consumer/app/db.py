import os
import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ["DATABASE_URL"]


def get_conn():
    return psycopg2.connect(DATABASE_URL)


def insert_transaction(event_id, payment_type, amount, status, partition, offset):
    query = """
        INSERT INTO transactions (event_id, payment_type, amount, status, partition, kafka_offset)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (event_id) DO NOTHING
        RETURNING id, event_id, payment_type, amount, status, partition, kafka_offset, created_at;
    """
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, (event_id, payment_type, amount, status, partition, offset))
            row = cur.fetchone()
            conn.commit()
            return dict(row) if row else None


def get_history(limit=50):
    query = "SELECT * FROM transactions ORDER BY created_at DESC LIMIT %s;"
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, (limit,))
            rows = [dict(r) for r in cur.fetchall()]
            for r in rows:
                r["amount"] = float(r["amount"])
                r["created_at"] = r["created_at"].isoformat()
            return rows


def reset_history():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE transactions RESTART IDENTITY;")
            conn.commit()


def get_stats():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) AS total FROM transactions;")
            total = cur.fetchone()["total"]

            cur.execute("""
                SELECT partition, COUNT(*) AS count FROM transactions
                GROUP BY partition ORDER BY partition;
            """)
            by_partition = [dict(r) for r in cur.fetchall()]

            cur.execute("""
                SELECT payment_type, COUNT(*) AS count FROM transactions
                GROUP BY payment_type;
            """)
            by_type = {r["payment_type"]: r["count"] for r in cur.fetchall()}

    return {"total": total, "byPartition": by_partition, "byType": by_type}
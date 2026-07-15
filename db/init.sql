CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    event_id UUID NOT NULL UNIQUE,
    payment_type VARCHAR(20) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'processed',
    partition INT NOT NULL,
    kafka_offset BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions (created_at DESC);
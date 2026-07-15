export interface TransactionRow {
  id: number;
  event_id: string;
  payment_type: string;
  amount: string;
  status: string;
  partition: number;
  kafka_offset: string;
  created_at: string;
}

export interface StreamMessage {
  type: "transaction" | "reset";
  partition?: number;
  row?: TransactionRow;
  sentAtMs?: number;
}
<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import PaymentButtons from "./components/PaymentButtons.svelte";
  import PartitionLanes from "./components/PartitionLanes.svelte";
  import ClusterState from "./components/ClusterState.svelte";
  import ConsumerGroupState from "./components/ConsumerGroupState.svelte";
  import StatsBar from "./components/StatsBar.svelte";
  import { createSSEConnection } from "./lib/sse";
  import type { TransactionRow, StreamMessage } from "./lib/types";

  const PRODUCER_URL = import.meta.env.VITE_PRODUCER_URL || "http://localhost:4000";
  const CONSUMER_URL = import.meta.env.VITE_CONSUMER_URL || "http://localhost:4001";
  const MAX_DOTS_PER_LANE = 8;

  let lanes: Record<string, TransactionRow[]> = { card: [], crypto: [], bank: [], wallet: [] };
  let history: TransactionRow[] = [];
  let lastLatencyMs: number | null = null;
  let connected = false;

  async function loadHistory() {
    try {
      const res = await fetch(`${CONSUMER_URL}/api/history`);
      history = await res.json();
    } catch (err) {
      console.error("Failed to load history:", err);
    }
  }

  function handleMessage(msg: StreamMessage) {
    if (msg.type === "reset") {
      lanes = { card: [], crypto: [], bank: [], wallet: [] };
      history = [];
      lastLatencyMs = null;
      return;
    }

    if (msg.type === "transaction" && msg.row) {
      const row = msg.row;
      lanes = {
        ...lanes,
        [row.payment_type]: [row, ...(lanes[row.payment_type] || [])].slice(0, MAX_DOTS_PER_LANE),
      };
      history = [row, ...history].slice(0, 50);

      if (msg.sentAtMs) {
        lastLatencyMs = Date.now() - msg.sentAtMs;
      }
    }
  }

  let sse: ReturnType<typeof createSSEConnection>;

  onMount(() => {
    loadHistory();
    sse = createSSEConnection(`${CONSUMER_URL}/api/stream`, handleMessage);
    sse.connected.subscribe((v) => (connected = v));
  });

  onDestroy(() => sse?.close());

  async function handleReset() {
    try {
      await fetch(`${CONSUMER_URL}/api/reset`, { method: "POST" });
    } catch (err) {
      console.error("Failed to reset:", err);
    }
  }
</script>

<div class="app">
  <div class="header">
    <div>
      <h1>payflow</h1>
      <div class="subtitle">
        {connected ? "● live" : "○ connecting..."} — 3-broker KRaft cluster, 4 partitions, RF=3
      </div>
    </div>
    <button class="reset-btn" on:click={handleReset}>Reset</button>
  </div>

  <StatsBar consumerUrl={CONSUMER_URL} {lastLatencyMs} />
  <PaymentButtons producerUrl={PRODUCER_URL} />

  <div class="grid">
    <div class="panel">
      <h2>Partition Lanes</h2>
      <PartitionLanes recentByPartitionType={lanes} />
    </div>
    <div style="display: flex; flex-direction: column; gap: 20px;">
      <ClusterState producerUrl={PRODUCER_URL} />
      <ConsumerGroupState consumerUrl={CONSUMER_URL} />
    </div>
  </div>

  <div class="panel" style="margin-top: 20px;">
    <h2>Recent Transactions</h2>
    <div style="max-height: 400px; overflow-y: auto;">
    {#each history as row (row.event_id)}
      <div class="history-row">
        <span>{new Date(row.created_at).toLocaleTimeString()}</span>
        <span class="type-{row.payment_type}">{row.payment_type}</span>
        <span>${row.amount}</span>
        <span>p{row.partition}</span>
      </div>
    {/each}
    {#if history.length === 0}
      <p style="color: var(--muted); font-size: 13px;">No transactions yet. Click a button above.</p>
    {/if}
    </div>
  </div>
</div>
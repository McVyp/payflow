<script lang="ts">
  import { onMount, onDestroy } from "svelte";

  export let consumerUrl: string;
  export let lastLatencyMs: number | null;

  interface Stats {
    total: number;
    byPartition: { partition: number; count: number }[];
    byType: Record<string, number>;
  }

  let stats: Stats | null = null;
  let interval: ReturnType<typeof setInterval>;

  async function poll() {
    try {
      const res = await fetch(`${consumerUrl}/api/stats`);
      stats = await res.json();
    } catch (err) {
      console.error("Failed to poll stats:", err);
    }
  }

  onMount(() => {
    poll();
    interval = setInterval(poll, 2000);
  });

  onDestroy(() => clearInterval(interval));
</script>

<div class="panel" style="margin-bottom: 20px;">
  <h2>Live Stats</h2>
  <div class="kv-row">
    <span class="k">Total committed</span>
    <span>{stats ? stats.total : "…"}</span>
  </div>
  <div class="kv-row">
    <span class="k">Last click → dot latency</span>
    <span>{lastLatencyMs !== null ? `${lastLatencyMs} ms` : "—"}</span>
  </div>
  {#if stats}
    {#each stats.byPartition as p (p.partition)}
      <div class="kv-row">
        <span class="k">Partition {p.partition} total</span>
        <span>{p.count}</span>
      </div>
    {/each}
  {/if}
</div>
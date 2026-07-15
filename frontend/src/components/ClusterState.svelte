<script lang="ts">
  import { onMount, onDestroy } from "svelte";

  export let producerUrl: string;

  interface ClusterInfo {
    brokers: { nodeId: number; host: string; port: number }[];
    controller: number;
    clusterId: string;
    topic: {
      name: string;
      partitions: { partitionId: number; leader: number; replicas: number[]; isr: number[] }[];
    };
  }

  let cluster: ClusterInfo | null = null;
  let interval: ReturnType<typeof setInterval>;

  async function poll() {
    try {
      const res = await fetch(`${producerUrl}/api/cluster`);
      cluster = await res.json();
    } catch (err) {
      console.error("Failed to poll cluster state:", err);
    }
  }

  onMount(() => {
    poll();
    interval = setInterval(poll, 3000);
  });

  onDestroy(() => clearInterval(interval));
</script>

<div class="panel">
  <h2>Cluster State</h2>
  {#if !cluster}
    <p style="color: var(--muted); font-size: 13px;">Connecting...</p>
  {:else}
    <div class="kv-row"><span class="k">Brokers</span><span>{cluster.brokers.length}</span></div>
    <div class="kv-row"><span class="k">Active Controller</span><span>Broker {cluster.controller}</span></div>
    <div class="kv-row"><span class="k">Topic</span><span>{cluster.topic.name}</span></div>
    {#each cluster.topic.partitions as p (p.partitionId)}
      <div class="kv-row">
        <span class="k">Partition {p.partitionId}</span>
        <span>leader={p.leader} isr=[{p.isr.join(",")}]</span>
      </div>
    {/each}
  {/if}
</div>
<script lang="ts">
  import { onMount, onDestroy } from "svelte";

  export let consumerUrl: string;

  interface GroupInfo {
    groupId: string;
    state: string;
    protocol: string;
    members: { memberId: string; clientId: string; clientHost: string }[];
    lagByPartition: { partition: number; committedOffset: number; highWatermark: number; lag: number }[];
  }

  let group: GroupInfo | null = null;
  let interval: ReturnType<typeof setInterval>;

  async function poll() {
    try {
      const res = await fetch(`${consumerUrl}/api/group`);
      group = await res.json();
    } catch (err) {
      console.error("Failed to poll group state:", err);
    }
  }

  onMount(() => {
    poll();
    interval = setInterval(poll, 3000);
  });

  onDestroy(() => clearInterval(interval));
</script>

<div class="panel">
  <h2>Consumer Group</h2>
  {#if !group}
    <p style="color: var(--muted); font-size: 13px;">Connecting...</p>
  {:else}
    <div class="kv-row"><span class="k">Group ID</span><span>{group.groupId}</span></div>
    <div class="kv-row"><span class="k">State</span><span><span class="badge ok">{group.state}</span></span></div>
    <div class="kv-row"><span class="k">Members</span><span>{group.members.length}</span></div>
    {#each group.lagByPartition as p (p.partition)}
      <div class="kv-row">
        <span class="k">Partition {p.partition} lag</span>
        <span>{p.lag}</span>
      </div>
    {/each}
  {/if}
</div>
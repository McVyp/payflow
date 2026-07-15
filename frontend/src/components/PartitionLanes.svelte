<script lang="ts">
  import { fly, fade } from "svelte/transition";
  import type { TransactionRow } from "../lib/types";

  export let recentByPartitionType: Record<string, TransactionRow[]>;

  const LANE_ORDER = ["card", "crypto", "bank", "wallet"] as const;
</script>

<div class="lanes">
  {#each LANE_ORDER as type}
    <div class="lane">
      <div class="lane-label">{type}</div>
      {#each recentByPartitionType[type] || [] as row (row.event_id)}
        <div
          class="dot {type}"
          title={`$${row.amount} · partition ${row.partition}`}
          in:fly={{ y: -12, duration: 250 }}
          out:fade={{ duration: 150 }}
        ></div>
      {/each}
    </div>
  {/each}
</div>
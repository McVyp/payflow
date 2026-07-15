<script lang="ts">
  export let producerUrl: string;
  export let disabled = false;

  const PAYMENT_TYPES = ["card", "crypto", "bank", "wallet"] as const;
  type PaymentType = (typeof PAYMENT_TYPES)[number];

  const LABELS: Record<PaymentType, string> = {
    card: "Card Payment",
    crypto: "Crypto Transfer",
    bank: "Bank Transfer",
    wallet: "Wallet Top-up",
  };

  async function handleClick(paymentType: PaymentType) {
    try {
      await fetch(`${producerUrl}/api/click`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ paymentType }),
      });
    } catch (err) {
      console.error("Failed to send payment event:", err);
    }
  }
</script>

<div class="buttons">
  {#each PAYMENT_TYPES as type}
    <button class="pay-btn {type}" {disabled} on:click={() => handleClick(type)}>
      {LABELS[type]}
    </button>
  {/each}
</div>
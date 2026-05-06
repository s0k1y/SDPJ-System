<template>
  <tbody>
    <tr v-for="n in rows" :key="n" class="skeleton-row">
      <td v-for="c in cols" :key="c">
        <div class="skeleton-shimmer"></div>
      </td>
    </tr>
  </tbody>
</template>

<script setup>
defineProps({
  rows: { type: Number, default: 1 },
  cols: { type: Number, default: 4 }
})
</script>

<style scoped>
.skeleton-row td {
  padding: 10px 8px;
  vertical-align: middle;
}

.skeleton-shimmer {
  height: 16px;
  border-radius: 6px;
  background: linear-gradient(
    100deg,
    var(--shimmer-color-base) 40%,
    var(--shimmer-color-highlight) 50%,
    var(--shimmer-color-base) 60%
  );
  background-size: 200% 100%;
  animation: shimmer var(--shimmer-duration) ease-in-out infinite;
}
</style>

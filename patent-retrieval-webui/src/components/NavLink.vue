<template>
  <router-link
    :to="to"
    class="px-4 py-2 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-all flex items-center gap-2"
    active-class="bg-purple-500/30 text-white"
  >
    <slot />
  </router-link>
</template>

<script setup lang="ts">
defineProps<{
  to: string;
}>();
</script>

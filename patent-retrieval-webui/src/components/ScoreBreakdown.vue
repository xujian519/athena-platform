<template>
  <div class="grid grid-cols-3 gap-3">
    <div class="bg-blue-500/10 rounded-lg p-3 border border-blue-500/20">
      <div class="text-blue-300 text-xs mb-1">
        全文搜索
      </div>
      <div class="text-white font-bold">
        {{ (breakdown.fulltext * 100).toFixed(1) }}%
      </div>
      <div class="text-blue-300 text-xs">
        {{ breakdown.fulltext.toFixed(3) }}
      </div>
    </div>

    <div class="bg-purple-500/10 rounded-lg p-3 border border-purple-500/20">
      <div class="text-purple-300 text-xs mb-1">
        向量检索
      </div>
      <div class="text-white font-bold">
        {{ (breakdown.vector * 100).toFixed(1) }}%
      </div>
      <div class="text-purple-300 text-xs">
        {{ breakdown.vector.toFixed(3) }}
      </div>
    </div>

    <div class="bg-green-500/10 rounded-lg p-3 border border-green-500/20">
      <div class="text-green-300 text-xs mb-1">
        知识图谱
      </div>
      <div class="text-white font-bold">
        {{ (breakdown.kg * 100).toFixed(1) }}%
      </div>
      <div class="text-green-300 text-xs">
        {{ breakdown.kg.toFixed(3) }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  breakdown: {
    fulltext: number;
    vector: number;
    kg: number;
    weights: {
      fulltext: number;
      vector: number;
      kg: number;
    };
  };
}

const props = defineProps<Props>();

const breakdown = computed(() => {
  const max = Math.max(
    props.breakdown.fulltext,
    props.breakdown.vector,
    props.breakdown.kg
  ) || 1;
  return {
    fulltext: props.breakdown.fulltext / max,
    vector: props.breakdown.vector / max,
    kg: props.breakdown.kg / max,
  };
});
</script>

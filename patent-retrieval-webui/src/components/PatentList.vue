<template>
  <div class="space-y-4 animate-fade-in">
    <div
      v-for="(result, index) in sortedResults"
      :key="result.patent_id"
      class="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20 hover:border-purple-400/50 transition-all cursor-pointer"
      :style="{ animationDelay: `${index * 50}ms` }"
      @click="handleClick(result)"
    >
      <div class="flex items-start justify-between mb-4">
        <div class="flex-1">
          <div class="flex items-center gap-2 mb-2">
            <span class="px-2 py-1 bg-purple-500/20 text-purple-300 text-xs rounded-full">
              #{{ index + 1 }}
            </span>
            <span
              v-for="source in result.metadata.sources"
              :key="source"
              class="px-2 py-1 text-xs rounded-full"
              :class="getSourceColor(source)"
            >
              {{ source }}
            </span>
          </div>
          <h3 class="text-xl font-bold text-white mb-2">
            {{ result.title }}
          </h3>
          <p class="text-purple-200 text-sm mb-3">
            专利ID: {{ result.patent_id }}
          </p>
        </div>
        <div class="text-right">
          <div class="text-2xl font-bold text-white">
            {{ result.score.toFixed(3) }}
          </div>
          <div class="text-purple-300 text-sm">
            综合评分
          </div>
        </div>
      </div>

      <p class="text-gray-300 mb-4 line-clamp-3">
        {{ result.abstract }}
      </p>

      <div
        v-if="result.evidence"
        class="bg-purple-500/10 rounded-lg p-3 mb-4"
      >
        <p class="text-purple-200 text-sm">
          <span class="font-semibold">匹配证据：</span>
          <span v-html="result.evidence" />
        </p>
      </div>

      <ScoreBreakdown
        v-if="result.metadata.score_breakdown"
        :breakdown="result.metadata.score_breakdown"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { RetrievalResult } from '@/types';
import ScoreBreakdown from './ScoreBreakdown.vue';

interface Props {
  results: RetrievalResult[];
}

const props = defineProps<Props>();

const emit = defineEmits<{
  select: [patentId: string];
}>();

const sortedResults = computed(() => {
  return [...props.results].sort((a, b) => b.score - a.score);
});

function getSourceColor(source: string): string {
  if (source.startsWith('FT')) {
    return 'bg-blue-500/20 text-blue-300';
  }
  if (source.startsWith('VEC')) {
    return 'bg-purple-500/20 text-purple-300';
  }
  if (source.startsWith('KG')) {
    return 'bg-green-500/20 text-green-300';
  }
  return 'bg-gray-500/20 text-gray-300';
}

function handleClick(result: RetrievalResult) {
  emit('select', result.patent_id);
}
</script>

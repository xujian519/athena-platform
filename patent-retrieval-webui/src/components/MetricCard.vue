<template>
  <div class="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
    <div class="flex items-center gap-4 mb-4">
      <div class="text-4xl">
        {{ icon }}
      </div>
      <div class="flex-1">
        <div class="text-purple-200 text-sm">
          {{ title }}
        </div>
        <div class="text-3xl font-bold text-white">
          {{ formattedValue }}
        </div>
      </div>
    </div>
    <div
      v-if="format === 'percent'"
      class="w-full bg-gray-700 rounded-full h-2"
    >
      <div
        class="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full transition-all"
        :style="{ width: `${value}%` }"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  title: string;
  value: number;
  format?: 'percent' | 'ms' | 'number';
  icon?: string;
}

const props = withDefaults(defineProps<Props>(), {
  format: 'number',
  icon: '📊',
});

const formattedValue = computed(() => {
  switch (props.format) {
    case 'percent':
      return `${(props.value * 100).toFixed(1)}%`;
    case 'ms':
      return `${props.value.toFixed(0)}ms`;
    case 'number':
    default:
      return props.value.toLocaleString();
  }
});
</script>

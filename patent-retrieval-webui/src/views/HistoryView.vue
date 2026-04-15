<template>
  <div class="bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 min-h-screen p-8">
    <div class="max-w-7xl mx-auto">
      <h1 class="text-4xl font-bold text-white mb-8">
        搜索历史
      </h1>

      <div
        v-if="history.length === 0"
        class="text-center py-16"
      >
        <svg
          class="w-24 h-24 text-purple-400 mx-auto mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <p class="text-xl text-purple-200">
          暂无搜索历史
        </p>
      </div>

      <div
        v-else
        class="space-y-4"
      >
        <div
          v-for="item in history"
          :key="item.id"
          class="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20 hover:border-purple-400/50 transition-all cursor-pointer"
          @click="handleReplay(item)"
        >
          <div class="flex items-start justify-between mb-4">
            <div class="flex-1">
              <h3 class="text-xl font-bold text-white mb-2">
                {{ item.query }}
              </h3>
              <div class="flex gap-4 text-purple-200 text-sm">
                <span>{{ formatDate(item.timestamp) }}</span>
                <span>{{ item.results_count }} 条结果</span>
              </div>
            </div>
            <button
              @click.stop="handleDelete(item.id)"
              class="p-2 hover:bg-red-500/20 rounded-lg transition-colors"
            >
              <svg
                class="w-5 h-5 text-red-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
          </div>

          <div
            v-if="item.results && item.results.length > 0"
            class="grid grid-cols-1 md:grid-cols-3 gap-3"
          >
            <div
              v-for="result in item.results.slice(0, 3)"
              :key="result.patent_id"
              class="bg-purple-500/10 rounded-lg p-3"
            >
              <p class="text-white text-sm font-medium truncate">
                {{ result.title }}
              </p>
              <p class="text-purple-300 text-xs">
                {{ result.score.toFixed(3) }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <button
        v-if="history.length > 0"
        @click="handleClearAll"
        class="mt-8 px-6 py-3 bg-red-500/20 text-red-300 rounded-xl hover:bg-red-500/30 transition-colors"
      >
        清空所有历史
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { computed } from 'vue';
import { useSearchStore } from '@/stores/search';
import type { SearchHistory } from '@/types';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';

const router = useRouter();
const searchStore = useSearchStore();

const history = computed(() => searchStore.history);

function formatDate(dateString: string): string {
  return format(new Date(dateString), 'yyyy-MM-dd HH:mm:ss', { locale: zhCN });
}

function handleReplay(item: SearchHistory) {
  searchStore.search(item.query);
  router.push('/');
}

function handleDelete(id: string) {
  const index = history.value.findIndex((h) => h.id === id);
  if (index > -1) {
    history.value.splice(index, 1);
  }
}

function handleClearAll() {
  if (confirm('确定要清空所有搜索历史吗？')) {
    searchStore.clearHistory();
  }
}
</script>

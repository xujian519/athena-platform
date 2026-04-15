<template>
  <div class="bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 min-h-screen p-8">
    <div class="max-w-7xl mx-auto">
      <div
        class="text-center mb-12 animate-fade-in"
      >
        <h1 class="text-5xl font-bold text-white mb-4 tracking-tight">
          专利混合检索系统
        </h1>
        <p class="text-xl text-purple-200">
          Patent Hybrid Retrieval System
        </p>
      </div>

      <div
        class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8"
      >
        <div
          class="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20"
        >
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-full bg-blue-500/20 flex items-center justify-center">
              <svg
                class="w-6 h-6 text-blue-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <div>
              <h3 class="text-white font-semibold">
                BM25 全文搜索
              </h3>
              <p class="text-purple-200 text-sm">权重: {{ (weights.fulltext * 100).toFixed(0) }}%</p>
            </div>
          </div>
        </div>

        <div
          class="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20"
        >
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-full bg-purple-500/20 flex items-center justify-center">
              <svg
                class="w-6 h-6 text-purple-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <div>
              <h3 class="text-white font-semibold">
                向量语义检索
              </h3>
              <p class="text-purple-200 text-sm">权重: {{ (weights.vector * 100).toFixed(0) }}%</p>
            </div>
          </div>
        </div>

        <div
          class="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20"
        >
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center">
              <svg
                class="w-6 h-6 text-green-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
            </div>
            <div>
              <h3 class="text-white font-semibold">
                知识图谱增强
              </h3>
              <p class="text-purple-200 text-sm">权重: {{ (weights.kg * 100).toFixed(0) }}%</p>
            </div>
          </div>
        </div>
      </div>

      <SearchForm @search="handleSearch" />

      <div
        v-if="isSearching"
        class="mt-8 text-center"
      >
        <div class="inline-flex items-center gap-2 text-white">
          <svg
            class="animate-spin h-5 w-5 text-purple-400"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
            />
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          <span>正在检索专利数据...</span>
        </div>
      </div>

      <PatentList
        v-else-if="hasResults"
        :results="results"
        @select="handleSelectPatent"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import SearchForm from '@/components/SearchForm.vue';
import PatentList from '@/components/PatentList.vue';
import { useSearchStore } from '@/stores/search';
import { useConfigStore } from '@/stores/config';

const searchStore = useSearchStore();
const configStore = useConfigStore();

const query = computed(() => searchStore.query);
const results = computed(() => searchStore.results);
const isSearching = computed(() => searchStore.loading);
const hasResults = computed(() => searchStore.hasResults);
const weights = computed(() => configStore.weights);

onMounted(() => {
  configStore.loadSystemStats();
});

function handleSearch(searchQuery: string) {
  searchStore.search(searchQuery);
}

function handleSelectPatent(patentId: string) {
  searchStore.selectPatent(patentId);
}
</script>

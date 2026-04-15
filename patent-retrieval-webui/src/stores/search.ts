import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { SearchHistory, RetrievalResult, ConfigWeights } from '@/types';
import { apiClient } from '@/api/client';

export const useSearchStore = defineStore('search', () => {
  const query = ref('');
  const results = ref<RetrievalResult[]>([]);
  const loading = ref(false);
  const history = ref<SearchHistory[]>([]);
  const selectedPatentId = ref<string | null>(null);

  const hasResults = computed(() => results.value.length > 0);
  const isSearching = computed(() => loading.value);

  async function search(queryText: string, topK: number = 20) {
    loading.value = true;
    query.value = queryText;
    results.value = [];

    try {
      const response = await apiClient.search({
        query: queryText,
        top_k: topK,
      });

      results.value = response.results;

      const historyItem: SearchHistory = {
        id: Date.now().toString(),
        query: queryText,
        timestamp: new Date().toISOString(),
        results_count: response.results.length,
        results: response.results,
      };

      history.value.unshift(historyItem);

      if (history.value.length > 100) {
        history.value = history.value.slice(0, 100);
      }
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      loading.value = false;
    }
  }

  function clearResults() {
    results.value = [];
    query.value = '';
  }

  function selectPatent(patentId: string) {
    selectedPatentId.value = patentId;
  }

  function clearSelection() {
    selectedPatentId.value = null;
  }

  function getHistoryById(id: string): SearchHistory | undefined {
    return history.value.find((item) => item.id === id);
  }

  function clearHistory() {
    history.value = [];
  }

  return {
    query,
    results,
    loading,
    history,
    selectedPatentId,
    hasResults,
    isSearching,
    search,
    clearResults,
    selectPatent,
    clearSelection,
    getHistoryById,
    clearHistory,
  };
});

import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { SystemStats, ConfigWeights, MonitoringMetrics } from '@/types';
import { apiClient } from '@/api/client';

export const useConfigStore = defineStore('config', () => {
  const weights = ref<ConfigWeights>({
    fulltext: 0.4,
    vector: 0.5,
    kg: 0.1,
  });

  const systemStats = ref<SystemStats | null>(null);
  const monitoringMetrics = ref<MonitoringMetrics | null>(null);
  const loading = ref(false);

  async function loadSystemStats() {
    try {
      systemStats.value = await apiClient.getSystemStats();
      if (systemStats.value) {
        weights.value = systemStats.value.weights;
      }
    } catch (error) {
      console.error('Failed to load system stats:', error);
    }
  }

  async function loadMonitoringMetrics() {
    try {
      monitoringMetrics.value = await apiClient.getMonitoringMetrics();
    } catch (error) {
      console.error('Failed to load monitoring metrics:', error);
    }
  }

  async function updateWeights(newWeights: ConfigWeights) {
    loading.value = true;
    try {
      await apiClient.updateWeights(newWeights);
      weights.value = newWeights;
    } catch (error) {
      console.error('Failed to update weights:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  function validateWeights(
    newWeights: ConfigWeights
  ): { valid: boolean; error?: string } {
    const total =
      newWeights.fulltext + newWeights.vector + newWeights.kg;

    if (Math.abs(total - 1.0) > 0.01) {
      return {
        valid: false,
        error: `权重总和必须为1.0，当前为${total.toFixed(2)}`,
      };
    }

    if (
      newWeights.fulltext < 0 ||
      newWeights.fulltext > 1 ||
      newWeights.vector < 0 ||
      newWeights.vector > 1 ||
      newWeights.kg < 0 ||
      newWeights.kg > 1
    ) {
      return { valid: false, error: '所有权重必须在0到1之间' };
    }

    return { valid: true };
  }

  return {
    weights,
    systemStats,
    monitoringMetrics,
    loading,
    loadSystemStats,
    loadMonitoringMetrics,
    updateWeights,
    validateWeights,
  };
});

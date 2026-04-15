<template>
  <div class="bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 min-h-screen p-8">
    <div class="max-w-4xl mx-auto">
      <h1 class="text-4xl font-bold text-white mb-8">
        系统配置
      </h1>

      <div
        class="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 mb-8"
      >
        <h2 class="text-2xl font-bold text-white mb-6">
          检索权重配置
        </h2>

        <div class="space-y-6">
          <div>
            <label class="flex justify-between text-white font-medium mb-2">
              <span>BM25 全文搜索权重</span>
              <span>{{ (localWeights.fulltext * 100).toFixed(0) }}%</span>
            </label>
            <input
              v-model.number="localWeights.fulltext"
              type="range"
              min="0"
              max="1"
              step="0.05"
              class="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
            />
          </div>

          <div>
            <label class="flex justify-between text-white font-medium mb-2">
              <span>向量语义检索权重</span>
              <span>{{ (localWeights.vector * 100).toFixed(0) }}%</span>
            </label>
            <input
              v-model.number="localWeights.vector"
              type="range"
              min="0"
              max="1"
              step="0.05"
              class="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
            />
          </div>

          <div>
            <label class="flex justify-between text-white font-medium mb-2">
              <span>知识图谱增强权重</span>
              <span>{{ (localWeights.kg * 100).toFixed(0) }}%</span>
            </label>
            <input
              v-model.number="localWeights.kg"
              type="range"
              min="0"
              max="1"
              step="0.05"
              class="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
            />
          </div>

          <div class="bg-purple-500/10 rounded-lg p-4">
            <p class="text-purple-200 text-sm">
              权重总和: <span class="font-bold">{{ totalWeight.toFixed(2) }}</span>
              <span
                v-if="!isValid"
                class="ml-2 text-red-400"
              >（必须为1.0）</span>
            </p>
          </div>

          <button
            @click="handleSave"
            :disabled="!isValid || loading"
            class="w-full py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold rounded-xl hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {{ loading ? '保存中...' : '保存配置' }}
          </button>
        </div>
      </div>

      <div
        v-if="systemStats"
        class="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20"
      >
        <h2 class="text-2xl font-bold text-white mb-6">
          系统状态
        </h2>

        <div class="grid grid-cols-2 gap-4">
          <div class="bg-green-500/10 rounded-lg p-4">
            <div class="text-green-300 text-sm mb-1">
              PostgreSQL
            </div>
            <div class="text-white font-bold">
              {{ systemStats.components.postgresql ? '运行中' : '未连接' }}
            </div>
          </div>

          <div class="bg-green-500/10 rounded-lg p-4">
            <div class="text-green-300 text-sm mb-1">
              Qdrant
            </div>
            <div class="text-white font-bold">
              {{ systemStats.components.qdrant ? '运行中' : '未连接' }}
            </div>
          </div>

          <div class="bg-green-500/10 rounded-lg p-4">
            <div class="text-green-300 text-sm mb-1">
              Neo4j
            </div>
            <div class="text-white font-bold">
              {{ systemStats.components.neo4j ? '运行中' : '未连接' }}
            </div>
          </div>

          <div class="bg-purple-500/10 rounded-lg p-4">
            <div class="text-purple-300 text-sm mb-1">
              专利数量
            </div>
            <div class="text-white font-bold">
              {{ systemStats.patent_count?.toLocaleString() || '未知' }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useConfigStore } from '@/stores/config';

const configStore = useConfigStore();

const localWeights = ref({ ...configStore.weights });
const loading = ref(false);
const systemStats = computed(() => configStore.systemStats);

const totalWeight = computed(() => {
  return localWeights.value.fulltext + localWeights.value.vector + localWeights.value.kg;
});

const isValid = computed(() => {
  const validation = configStore.validateWeights(localWeights.value);
  return validation.valid;
});

watch(
  () => configStore.weights,
  (newWeights) => {
    localWeights.value = { ...newWeights };
  },
  { deep: true }
);

async function handleSave() {
  loading.value = true;
  try {
    await configStore.updateWeights(localWeights.value);
    alert('配置已保存！');
  } catch (error) {
    alert('保存失败，请重试');
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  configStore.loadSystemStats();
});
</script>

<template>
  <div class="bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 min-h-screen p-8">
    <div class="max-w-7xl mx-auto">
      <h1 class="text-4xl font-bold text-white mb-8">
        实时监控
      </h1>

      <div
        v-if="loading"
        class="text-center py-16"
      >
        <svg
          class="animate-spin h-12 w-12 text-purple-400 mx-auto"
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
        <p class="text-xl text-purple-200 mt-4">
          加载监控数据...
        </p>
      </div>

      <div
        v-else-if="metrics"
        class="space-y-6"
      >
        <div
          class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
        >
          <MetricCard
            title="缓存命中率"
            :value="metrics.cache_hit_rate"
            format="percent"
            icon="📊"
          />

          <MetricCard
            title="平均响应时间"
            :value="metrics.avg_response_time"
            format="ms"
            icon="⚡"
          />

          <MetricCard
            title="活跃连接"
            :value="metrics.active_connections"
            format="number"
            icon="🔗"
          />

          <MetricCard
            title="错误率"
            :value="metrics.error_rate"
            format="percent"
            icon="❌"
          />
        </div>

        <div
          class="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20"
        >
          <h2 class="text-2xl font-bold text-white mb-6">
            查询频率
          </h2>
          <div
            ref="chartContainer"
            class="h-96"
          />
        </div>

        <div
          class="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20"
        >
          <h2 class="text-2xl font-bold text-white mb-6">
            性能指标趋势
          </h2>
          <div
            ref="performanceChartContainer"
            class="h-96"
          />
        </div>
      </div>

      <div
        v-else
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
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <p class="text-xl text-purple-200">
          暂无监控数据
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useConfigStore } from '@/stores/config';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import MetricCard from '@/components/MetricCard.vue';

const configStore = useConfigStore();

const loading = ref(true);
const metrics = ref(configStore.monitoringMetrics);
const chartContainer = ref<HTMLDivElement>();
const performanceChartContainer = ref<HTMLDivElement>();
let chartInstance: echarts.ECharts | null = null;
let performanceChartInstance: echarts.ECharts | null = null;
let updateInterval: number | null = null;

onMounted(async () => {
  await loadMetrics();
  initCharts();
  updateInterval = window.setInterval(loadMetrics, 5000);
});

onUnmounted(() => {
  if (updateInterval) {
    clearInterval(updateInterval);
  }
  if (chartInstance) {
    chartInstance.dispose();
  }
  if (performanceChartInstance) {
    performanceChartInstance.dispose();
  }
});

async function loadMetrics() {
  try {
    await configStore.loadMonitoringMetrics();
    metrics.value = configStore.monitoringMetrics;
    loading.value = false;
    updateCharts();
  } catch (error) {
    console.error('Failed to load metrics:', error);
  }
}

function initCharts() {
  if (chartContainer.value) {
    chartInstance = echarts.init(chartContainer.value);
    updateCharts();
  }

  if (performanceChartContainer.value) {
    performanceChartInstance = echarts.init(performanceChartContainer.value);
    updatePerformanceChart();
  }
}

function updateCharts() {
  if (!chartInstance) return;

  const option: EChartsOption = {
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: generateTimeLabels(10),
      axisLine: { lineStyle: { color: '#a78bfa' } },
      axisLabel: { color: '#e9d5ff' },
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#a78bfa' } },
      axisLabel: { color: '#e9d5ff' },
      splitLine: { lineStyle: { color: 'rgba(167, 139, 250, 0.1)' } },
    },
    series: [
      {
        name: '查询数',
        type: 'line',
        smooth: true,
        data: generateRandomData(10),
        lineStyle: { color: '#a855f7', width: 3 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(168, 85, 247, 0.5)' },
            { offset: 1, color: 'rgba(168, 85, 247, 0.1)' },
          ]),
        },
      },
    ],
  };

  chartInstance.setOption(option);
}

function updatePerformanceChart() {
  if (!performanceChartInstance) return;

  const option: EChartsOption = {
    legend: {
      data: ['响应时间', '缓存命中率'],
      textStyle: { color: '#e9d5ff' },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: generateTimeLabels(10),
      axisLine: { lineStyle: { color: '#a78bfa' } },
      axisLabel: { color: '#e9d5ff' },
    },
    yAxis: [
      {
        type: 'value',
        name: '响应时间(ms)',
        axisLine: { lineStyle: { color: '#a78bfa' } },
        axisLabel: { color: '#e9d5ff' },
        splitLine: { lineStyle: { color: 'rgba(167, 139, 250, 0.1)' } },
      },
      {
        type: 'value',
        name: '命中率(%)',
        min: 0,
        max: 100,
        axisLine: { lineStyle: { color: '#a78bfa' } },
        axisLabel: { color: '#e9d5ff' },
        splitLine: { lineStyle: { color: 'rgba(167, 139, 250, 0.1)' } },
      },
    ],
    series: [
      {
        name: '响应时间',
        type: 'line',
        yAxisIndex: 0,
        smooth: true,
        data: generateRandomData(10, 200, 500),
        lineStyle: { color: '#38bdf8', width: 3 },
      },
      {
        name: '缓存命中率',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        data: generateRandomData(10, 80, 95),
        lineStyle: { color: '#4ade80', width: 3 },
      },
    ],
  };

  performanceChartInstance.setOption(option);
}

function generateTimeLabels(count: number): string[] {
  const labels = [];
  const now = new Date();
  for (let i = count - 1; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 5000);
    labels.push(time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
  }
  return labels;
}

function generateRandomData(count: number, min: number = 10, max: number = 100): number[] {
  return Array.from({ length: count }, () => Math.floor(Math.random() * (max - min + 1)) + min);
}
</script>

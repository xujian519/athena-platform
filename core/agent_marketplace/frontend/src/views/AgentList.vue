<template>
  <div class="agent-list">
    <div class="filters">
      <h2>Agent市场</h2>

      <div class="filter-group">
        <input
          v-model="localFilters.keyword"
          type="text"
          placeholder="搜索Agent..."
          @input="onFilterChange"
          class="search-input"
        />

        <select
          v-model="localFilters.category"
          @change="onFilterChange"
          class="filter-select"
        >
          <option value="">所有分类</option>
          <option value="general">通用</option>
          <option value="patent">专利</option>
          <option value="legal">法律</option>
          <option value="ip">IP管理</option>
        </select>

        <select
          v-model.number="localFilters.minRating"
          @change="onFilterChange"
          class="filter-select"
        >
          <option value="">所有评分</option>
          <option value="4">4星及以上</option>
          <option value="3">3星及以上</option>
          <option value="2">2星及以上</option>
        </select>

        <select
          v-model="localFilters.sortBy"
          @change="onFilterChange"
          class="filter-select"
        >
          <option value="updated_at">最新更新</option>
          <option value="download_count">下载量</option>
          <option value="rating_avg">评分</option>
          <option value="name">名称</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading">
      加载中...
    </div>

    <div v-else-if="error" class="error">
      {{ error }}
    </div>

    <div v-else-if="!hasAgents" class="empty">
      暂无Agent
    </div>

    <div v-else>
      <div class="agent-grid">
        <AgentCard
          v-for="agent in agents"
          :key="agent.id"
          :agent="agent"
        />
      </div>

      <div class="pagination">
        <button
          :disabled="!hasPrevPage"
          @click="prevPage"
          class="btn btn-secondary"
        >
          上一页
        </button>
        <span class="page-info">
          第 {{ pagination.page }} / {{ pagination.totalPages }} 页
        </span>
        <button
          :disabled="!hasNextPage"
          @click="nextPage"
          class="btn btn-secondary"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useAgentStore } from '../stores/agent'
import AgentCard from '../components/AgentCard.vue'

const agentStore = useAgentStore()

const localFilters = ref({ ...agentStore.filters })

const loading = computed(() => agentStore.loading)
const error = computed(() => agentStore.error)
const agents = computed(() => agentStore.agents)
const hasAgents = computed(() => agentStore.hasAgents)
const pagination = computed(() => agentStore.pagination)
const hasNextPage = computed(() => agentStore.hasNextPage)
const hasPrevPage = computed(() => agentStore.hasPrevPage)

function onFilterChange() {
  agentStore.setFilters(localFilters.value)
  agentStore.fetchAgents(1)
}

function prevPage() {
  if (hasPrevPage.value) {
    agentStore.fetchAgents(pagination.value.page - 1)
  }
}

function nextPage() {
  if (hasNextPage.value) {
    agentStore.fetchAgents(pagination.value.page + 1)
  }
}

onMounted(() => {
  agentStore.fetchAgents()
})
</script>

<style scoped>
.agent-list {
  padding: 20px 0;
}

.filters {
  margin-bottom: 30px;
}

.filters h2 {
  margin-bottom: 20px;
}

.filter-group {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  min-width: 200px;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.filter-select {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  min-width: 120px;
}

.agent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
}

.page-info {
  color: #606266;
}

.empty {
  text-align: center;
  padding: 60px;
  color: #909399;
}
</style>

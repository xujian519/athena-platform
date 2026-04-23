<template>
  <div class="agent-detail">
    <div v-if="loading" class="loading">加载中...</div>

    <div v-else-if="error" class="error">{{ error }}</div>

    <div v-else-if="agent" class="detail-content">
      <div class="detail-header">
        <h1>{{ agent.display_name }}</h1>
        <div class="meta">
          <span class="version">v{{ agent.current_version }}</span>
          <span class="category">{{ categoryLabel }}</span>
          <span v-if="agent.featured" class="badge">精选</span>
          <span v-if="agent.verified" class="badge verified">认证</span>
        </div>
      </div>

      <div class="detail-body">
        <div class="main-content">
          <section class="description">
            <h2>简介</h2>
            <p>{{ agent.description }}</p>
            <p v-if="agent.long_description">{{ agent.long_description }}</p>
          </section>

          <section class="capabilities">
            <h2>能力</h2>
            <div v-if="capabilities.length > 0" class="capability-list">
              <div v-for="cap in capabilities" :key="cap.id" class="capability-item">
                <h4>{{ cap.display_name }}</h4>
                <p>{{ cap.description }}</p>
                <div class="capability-meta">
                  <span>输入: {{ cap.input_types.join(', ') }}</span>
                  <span>输出: {{ cap.output_types.join(', ') }}</span>
                  <span>耗时: {{ cap.estimated_time }}秒</span>
                </div>
              </div>
            </div>
            <div v-else class="empty">暂无能力信息</div>
          </section>

          <section class="stats">
            <h2>统计</h2>
            <div class="stats-grid">
              <div class="stat-item">
                <span class="stat-value">{{ agent.download_count }}</span>
                <span class="stat-label">下载量</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ agent.view_count }}</span>
                <span class="stat-label">浏览量</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ agent.rating_avg.toFixed(1) }}</span>
                <span class="stat-label">平均评分</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ agent.rating_count }}</span>
                <span class="stat-label">评价数</span>
              </div>
            </div>
          </section>
        </div>

        <div class="sidebar">
          <div class="card author-info">
            <h3>作者</h3>
            <p>{{ agent.author_name }}</p>
            <p v-if="agent.organization">{{ agent.organization }}</p>
          </div>

          <div class="card actions">
            <button class="btn btn-primary" @click="downloadAgent">
              下载Agent
            </button>
            <button class="btn btn-secondary" @click="starAgent">
              收藏
            </button>
          </div>

          <div class="card tech-info">
            <h3>技术要求</h3>
            <ul>
              <li>Python: {{ agent.python_version }}</li>
              <li v-if="agent.requires_llm">需要LLM</li>
              <li v-if="agent.requires_tools">需要工具系统</li>
            </ul>
          </div>

          <div class="card tags" v-if="agent.tags.length > 0">
            <h3>标签</h3>
            <div class="tag-list">
              <span v-for="tag in agent.tags" :key="tag" class="tag">
                {{ tag }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAgentStore } from '../stores/agent'

const route = useRoute()
const agentStore = useAgentStore()

const agent = ref(null)
const capabilities = ref([])
const loading = computed(() => agentStore.loading)
const error = computed(() => agentStore.error)

const categoryLabel = computed(() => {
  if (!agent.value) return ''
  const labels = {
    general: '通用',
    patent: '专利',
    legal: '法律',
    ip: 'IP管理',
  }
  return labels[agent.value.category] || agent.value.category
})

async function downloadAgent() {
  alert('下载功能待实现')
}

async function starAgent() {
  alert('收藏功能待实现')
}

onMounted(async () => {
  const id = route.params.id
  await agentStore.fetchAgent(id)
  agent.value = agentStore.currentAgent

  // 获取能力列表
  if (agent.value) {
    // TODO: 调用API获取能力
    capabilities.value = []
  }
})
</script>

<style scoped>
.agent-detail {
  padding: 20px 0;
}

.detail-header {
  margin-bottom: 30px;
}

.detail-header h1 {
  font-size: 32px;
  margin-bottom: 10px;
}

.meta {
  display: flex;
  gap: 10px;
  align-items: center;
}

.version {
  background: #f5f5f5;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 14px;
}

.category {
  background: #e6f7ff;
  color: #1890ff;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 14px;
}

.badge {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 14px;
}

.badge:first-child {
  background: #fff7e6;
  color: #fa8c16;
}

.badge.verified {
  background: #f6ffed;
  color: #52c41a;
}

.detail-body {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 30px;
}

.main-content > section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.main-content h2 {
  margin-bottom: 15px;
}

.capability-item {
  padding: 15px;
  border: 1px solid #eee;
  border-radius: 4px;
  margin-bottom: 10px;
}

.capability-item h4 {
  margin-bottom: 5px;
}

.capability-meta {
  display: flex;
  gap: 15px;
  font-size: 12px;
  color: #909399;
  margin-top: 10px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

.sidebar .card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.sidebar h3 {
  margin-bottom: 15px;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.actions button {
  width: 100%;
}

.tech-info ul {
  list-style: none;
  padding: 0;
}

.tech-info li {
  padding: 5px 0;
  border-bottom: 1px solid #eee;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  background: #f5f5f5;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
}

.empty {
  color: #909399;
  text-align: center;
  padding: 20px;
}

@media (max-width: 768px) {
  .detail-body {
    grid-template-columns: 1fr;
  }
}
</style>

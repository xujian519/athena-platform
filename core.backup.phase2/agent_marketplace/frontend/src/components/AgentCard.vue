<template>
  <div class="agent-card" @click="goToDetail">
    <div class="agent-header">
      <h3 class="agent-name">{{ agent.display_name }}</h3>
      <span class="agent-version">v{{ agent.current_version }}</span>
    </div>

    <p class="agent-description">{{ agent.description }}</p>

    <div class="agent-meta">
      <span class="agent-category">{{ categoryLabel }}</span>
      <span class="agent-author">{{ agent.author_name }}</span>
    </div>

    <div class="agent-stats">
      <div class="stat">
        <span class="stat-value">{{ agent.download_count }}</span>
        <span class="stat-label">下载</span>
      </div>
      <div class="stat">
        <span class="stat-value">{{ agent.rating_avg.toFixed(1) }}</span>
        <span class="stat-label">评分</span>
      </div>
      <div class="stat">
        <span class="stat-value">{{ agent.rating_count }}</span>
        <span class="stat-label">评价</span>
      </div>
    </div>

    <div class="agent-footer">
      <span v-if="agent.featured" class="badge badge-featured">精选</span>
      <span v-if="agent.verified" class="badge badge-verified">认证</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  agent: {
    type: Object,
    required: true,
  },
})

const router = useRouter()

const categoryLabel = computed(() => {
  const labels = {
    general: '通用',
    patent: '专利',
    legal: '法律',
    ip: 'IP管理',
  }
  return labels[props.agent.category] || props.agent.category
})

function goToDetail() {
  router.push({ name: 'AgentDetail', params: { id: props.agent.id } })
}
</script>

<style scoped>
.agent-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.agent-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.agent-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.agent-name {
  font-size: 18px;
  margin: 0;
  flex: 1;
}

.agent-version {
  font-size: 12px;
  color: #909399;
  background: #f5f5f5;
  padding: 2px 8px;
  border-radius: 12px;
}

.agent-description {
  color: #606266;
  font-size: 14px;
  margin-bottom: 15px;
  flex: 1;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.agent-meta {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
  font-size: 12px;
  color: #909399;
}

.agent-category {
  background: #e6f7ff;
  color: #1890ff;
  padding: 2px 8px;
  border-radius: 4px;
}

.agent-stats {
  display: flex;
  justify-content: space-around;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.stat {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 16px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.agent-footer {
  display: flex;
  gap: 5px;
  margin-top: 10px;
}

.badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
}

.badge-featured {
  background: #fff7e6;
  color: #fa8c16;
}

.badge-verified {
  background: #f6ffed;
  color: #52c41a;
}
</style>

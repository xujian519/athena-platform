<template>
  <div class="home">
    <section class="hero">
      <h1>欢迎使用Athena Agent市场</h1>
      <p>发现、分享和使用高质量的开源Agent</p>
      <div class="actions">
        <router-link to="/agents" class="btn btn-primary">浏览Agent</router-link>
        <router-link to="/agents/new" class="btn btn-secondary">发布Agent</router-link>
      </div>
    </section>

    <section class="stats">
      <div class="stat-item">
        <div class="stat-value">{{ stats.totalAgents }}</div>
        <div class="stat-label">Agent总数</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ stats.totalDownloads }}</div>
        <div class="stat-label">总下载量</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ stats.totalCategories }}</div>
        <div class="stat-label">分类数量</div>
      </div>
    </section>

    <section class="featured">
      <h2>精选Agent</h2>
      <div v-if="featuredAgents.length > 0" class="agent-grid">
        <AgentCard
          v-for="agent in featuredAgents"
          :key="agent.id"
          :agent="agent"
        />
      </div>
      <div v-else class="loading">加载中...</div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAgentStore } from '../stores/agent'
import AgentCard from '../components/AgentCard.vue'

const agentStore = useAgentStore()

const stats = ref({
  totalAgents: 0,
  totalDownloads: 0,
  totalCategories: 4,
})

const featuredAgents = ref([])

onMounted(async () => {
  // 获取精选Agent
  await agentStore.fetchAgents(1)
  featuredAgents.value = agentStore.agents.slice(0, 6)
})
</script>

<style scoped>
.home {
  padding: 40px 0;
}

.hero {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: 8px;
  margin-bottom: 40px;
}

.hero h1 {
  font-size: 48px;
  margin-bottom: 20px;
}

.hero p {
  font-size: 20px;
  color: #606266;
  margin-bottom: 30px;
}

.actions {
  display: flex;
  gap: 20px;
  justify-content: center;
}

.stats {
  display: flex;
  justify-content: center;
  gap: 60px;
  margin-bottom: 60px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 48px;
  font-weight: bold;
  color: #409eff;
}

.stat-label {
  font-size: 16px;
  color: #606266;
}

.featured h2 {
  margin-bottom: 20px;
}

.agent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}
</style>

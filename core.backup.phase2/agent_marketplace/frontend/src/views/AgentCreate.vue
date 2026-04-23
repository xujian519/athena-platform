<template>
  <div class="agent-create">
    <div class="form-container">
      <h1>发布新Agent</h1>

      <form @submit.prevent="handleSubmit" class="agent-form">
        <div class="form-group">
          <label for="name">Agent名称 (PascalCase) *</label>
          <input
            id="name"
            v-model="form.name"
            type="text"
            placeholder="例如: MyAgent"
            required
          />
        </div>

        <div class="form-group">
          <label for="displayName">显示名称 *</label>
          <input
            id="displayName"
            v-model="form.display_name"
            type="text"
            placeholder="例如: 我的Agent"
            required
          />
        </div>

        <div class="form-group">
          <label for="description">简短描述 *</label>
          <textarea
            id="description"
            v-model="form.description"
            placeholder="用一句话描述你的Agent..."
            rows="2"
            required
          ></textarea>
        </div>

        <div class="form-group">
          <label for="longDescription">详细描述</label>
          <textarea
            id="longDescription"
            v-model="form.long_description"
            placeholder="详细描述你的Agent功能、使用场景等..."
            rows="5"
          ></textarea>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="category">类别 *</label>
            <select id="category" v-model="form.category" required>
              <option value="general">通用</option>
              <option value="patent">专利</option>
              <option value="legal">法律</option>
              <option value="ip">IP管理</option>
            </select>
          </div>

          <div class="form-group">
            <label for="authorName">作者名称 *</label>
            <input
              id="authorName"
              v-model="form.author_name"
              type="text"
              placeholder="你的名字"
              required
            />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="authorId">作者ID *</label>
            <input
              id="authorId"
              v-model="form.author_id"
              type="text"
              placeholder="user_123"
              required
            />
          </div>

          <div class="form-group">
            <label for="organization">所属组织</label>
            <input
              id="organization"
              v-model="form.organization"
              type="text"
              placeholder="Athena平台"
            />
          </div>
        </div>

        <div class="form-group">
          <label>技术要求</label>
          <div class="checkbox-group">
            <label>
              <input type="checkbox" v-model="form.requires_llm" />
              需要LLM支持
            </label>
            <label>
              <input type="checkbox" v-model="form.requires_tools" />
              需要工具系统
            </label>
          </div>
        </div>

        <div class="form-group">
          <label for="tags">标签 (用逗号分隔)</label>
          <input
            id="tags"
            v-model="tagsInput"
            type="text"
            placeholder="例如: 自动化, 分析, 效率"
          />
        </div>

        <div class="form-actions">
          <button type="button" class="btn btn-secondary" @click="cancel">
            取消
          </button>
          <button type="submit" class="btn btn-primary" :disabled="submitting">
            {{ submitting ? '提交中...' : '发布Agent' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAgentStore } from '../stores/agent'

const router = useRouter()
const agentStore = useAgentStore()

const form = ref({
  name: '',
  display_name: '',
  description: '',
  long_description: '',
  category: 'general',
  author_name: '',
  author_id: '',
  organization: '',
  requires_llm: false,
  requires_tools: false,
  tags: [],
})

const tagsInput = ref('')
const submitting = ref(false)

async function handleSubmit() {
  submitting.value = true

  // 处理标签
  form.value.tags = tagsInput.value
    .split(',')
    .map(t => t.trim())
    .filter(t => t)

  try {
    await agentStore.createAgent(form.value)
    alert('Agent发布成功！')
    router.push({ name: 'AgentList' })
  } catch (err) {
    alert('发布失败：' + err.message)
  } finally {
    submitting.value = false
  }
}

function cancel() {
  router.push({ name: 'AgentList' })
}
</script>

<style scoped>
.agent-create {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px 0;
}

.form-container {
  background: white;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.agent-create h1 {
  margin-bottom: 30px;
}

.form-group {
  margin-bottom: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #409eff;
}

.checkbox-group {
  display: flex;
  gap: 20px;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-weight: normal;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  margin-top: 30px;
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>

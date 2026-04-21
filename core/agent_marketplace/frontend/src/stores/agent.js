import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

export const useAgentStore = defineStore('agent', () => {
  // 状态
  const agents = ref([])
  const currentAgent = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const pagination = ref({
    page: 1,
    pageSize: 20,
    total: 0,
    totalPages: 0,
  })

  // 过滤条件
  const filters = ref({
    keyword: '',
    category: null,
    status: null,
    minRating: null,
    sortBy: 'updated_at',
    sortOrder: 'desc',
  })

  // 计算属性
  const hasAgents = computed(() => agents.value.length > 0)
  const hasNextPage = computed(() => pagination.value.page < pagination.value.totalPages)
  const hasPrevPage = computed(() => pagination.value.page > 1)

  // Actions
  async function fetchAgents(page = 1) {
    loading.value = true
    error.value = null

    try {
      const params = {
        ...filters.value,
        page,
        page_size: pagination.value.pageSize,
      }

      const response = await api.get('/agents', { params })

      agents.value = response.items
      pagination.value = {
        page: response.page,
        pageSize: response.page_size,
        total: response.total,
        totalPages: response.total_pages,
      }
    } catch (err) {
      error.value = err.message || '获取Agent列表失败'
    } finally {
      loading.value = false
    }
  }

  async function fetchAgent(id) {
    loading.value = true
    error.value = null

    try {
      const response = await api.get(`/agents/${id}`)
      currentAgent.value = response
    } catch (err) {
      error.value = err.message || '获取Agent详情失败'
    } finally {
      loading.value = false
    }
  }

  async function createAgent(data) {
    loading.value = true
    error.value = null

    try {
      const response = await api.post('/agents', data)
      return response
    } catch (err) {
      error.value = err.message || '创建Agent失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateAgent(id, data) {
    loading.value = true
    error.value = null

    try {
      const response = await api.put(`/agents/${id}`, data)
      return response
    } catch (err) {
      error.value = err.message || '更新Agent失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteAgent(id) {
    loading.value = true
    error.value = null

    try {
      await api.delete(`/agents/${id}`)
    } catch (err) {
      error.value = err.message || '删除Agent失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  function setFilters(newFilters) {
    filters.value = { ...filters.value, ...newFilters }
  }

  function resetFilters() {
    filters.value = {
      keyword: '',
      category: null,
      status: null,
      minRating: null,
      sortBy: 'updated_at',
      sortOrder: 'desc',
    }
  }

  return {
    // 状态
    agents,
    currentAgent,
    loading,
    error,
    pagination,
    filters,

    // 计算属性
    hasAgents,
    hasNextPage,
    hasPrevPage,

    // Actions
    fetchAgents,
    fetchAgent,
    createAgent,
    updateAgent,
    deleteAgent,
    setFilters,
    resetFilters,
  }
})

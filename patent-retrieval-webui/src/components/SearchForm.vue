<template>
  <div class="max-w-4xl mx-auto mb-8">
    <form
      @submit.prevent="handleSubmit"
      class="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 shadow-xl"
    >
      <div class="mb-6">
        <label
          for="query"
          class="block text-white font-medium mb-2"
        >检索查询</label>
        <textarea
          id="query"
          v-model="searchQuery"
          rows="3"
          placeholder="输入专利关键词、技术领域或描述..."
          class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
        />
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div>
          <label
            class="block text-white font-medium mb-2"
          >返回结果数量</label>
          <select
            v-model.number="topK"
            class="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option :value="10">10 条</option>
            <option :value="20">20 条</option>
            <option :value="50">50 条</option>
            <option :value="100">100 条</option>
          </select>
        </div>

        <div>
          <label
            class="block text-white font-medium mb-2"
          >IPC分类代码</label>
          <input
            v-model="ipcCodes"
            type="text"
            placeholder="G06F, H04L..."
            class="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div>
          <label
            class="block text-white font-medium mb-2"
          >申请人</label>
          <input
            v-model="applicant"
            type="text"
            placeholder="输入申请人名称..."
            class="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        <div>
          <label
            class="block text-white font-medium mb-2"
          >发布日期范围</label>
          <div class="flex gap-2">
            <input
              v-model="dateStart"
              type="date"
              class="flex-1 px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <input
              v-model="dateEnd"
              type="date"
              class="flex-1 px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
        </div>
      </div>

      <button
        type="submit"
        :disabled="!searchQuery.trim()"
        class="w-full py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold rounded-xl hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-[1.02] active:scale-[0.98]"
      >
        开始检索
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const emit = defineEmits<{
  search: [query: string, topK: number];
}>();

const searchQuery = ref('');
const topK = ref(20);
const ipcCodes = ref('');
const applicant = ref('');
const dateStart = ref('');
const dateEnd = ref('');

function handleSubmit() {
  if (searchQuery.value.trim()) {
    emit('search', searchQuery.value, topK.value);
  }
}
</script>

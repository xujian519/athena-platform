<template>
  <nav class="bg-black/30 backdrop-blur-lg border-b border-white/10 sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-6">
      <div class="flex items-center justify-between h-16">
        <div class="flex items-center gap-8">
          <router-link
            to="/"
            class="flex items-center gap-2 group"
          >
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center group-hover:scale-110 transition-transform">
              <svg
                class="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <span class="text-xl font-bold text-white">
              专利检索
            </span>
          </router-link>

          <div class="hidden md:flex items-center gap-1">
            <NavLink to="/">
              检索
            </NavLink>
            <NavLink to="/history">
              历史
            </NavLink>
            <NavLink to="/config">
              配置
            </NavLink>
            <NavLink to="/monitoring">
              监控
            </NavLink>
          </div>
        </div>

        <div class="flex items-center gap-4">
          <div
            v-if="searchStore.isSearching"
            class="flex items-center gap-2 text-purple-300"
          >
            <svg
              class="animate-spin h-5 w-5"
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
            <span class="text-sm">检索中...</span>
          </div>

          <div
            v-if="searchStore.results.length > 0"
            class="px-3 py-1 bg-purple-500/20 rounded-full text-purple-300 text-sm"
          >
            {{ searchStore.results.length }} 结果
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { useSearchStore } from '@/stores/search';
import NavLink from './NavLink.vue';

const searchStore = useSearchStore();
</script>

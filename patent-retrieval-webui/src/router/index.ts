import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';
import SearchView from '@/views/SearchView.vue';
import HistoryView from '@/views/HistoryView.vue';
import ConfigView from '@/views/ConfigView.vue';
import MonitoringView from '@/views/MonitoringView.vue';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'search',
    component: SearchView,
  },
  {
    path: '/history',
    name: 'history',
    component: HistoryView,
  },
  {
    path: '/config',
    name: 'config',
    component: ConfigView,
  },
  {
    path: '/monitoring',
    name: 'monitoring',
    component: MonitoringView,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;

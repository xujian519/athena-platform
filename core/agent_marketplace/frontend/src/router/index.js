import { createRouter, createWebHistory } from 'vue-router'
import AgentList from '../views/AgentList.vue'
import AgentDetail from '../views/AgentDetail.vue'
import AgentCreate from '../views/AgentCreate.vue'
import Home from '../views/Home.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
  },
  {
    path: '/agents',
    name: 'AgentList',
    component: AgentList,
  },
  {
    path: '/agents/:id',
    name: 'AgentDetail',
    component: AgentDetail,
  },
  {
    path: '/agents/new',
    name: 'AgentCreate',
    component: AgentCreate,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
  { path: '/trades', name: 'Trades', component: () => import('../views/Trades.vue') },
  { path: '/risk', name: 'RiskEvents', component: () => import('../views/RiskEvents.vue') },
  { path: '/model', name: 'ModelStatus', component: () => import('../views/ModelStatus.vue') },
]

export default createRouter({ history: createWebHistory(), routes })

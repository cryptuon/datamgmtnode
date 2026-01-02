import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue')
  },
  {
    path: '/health',
    name: 'Health',
    component: () => import('@/views/Health.vue')
  },
  {
    path: '/tokens',
    name: 'Tokens',
    component: () => import('@/views/Tokens.vue')
  },
  {
    path: '/data',
    name: 'DataSharing',
    component: () => import('@/views/DataSharing.vue')
  },
  {
    path: '/compliance',
    name: 'Compliance',
    component: () => import('@/views/Compliance.vue')
  },
  {
    path: '/network',
    name: 'Network',
    component: () => import('@/views/Network.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

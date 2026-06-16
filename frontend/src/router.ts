import { createMemoryHistory, createRouter } from 'vue-router'
import Upload from './components/Upload.vue'
import About from './components/About.vue'
import Gallery from './components/Gallery.vue'

const routes = [
  { path: '/', component: Upload },
  { path: '/gallery', component: Gallery },
  { path: '/about', component: About },
]

export const router = createRouter({
  history: createMemoryHistory(),
  routes,
})
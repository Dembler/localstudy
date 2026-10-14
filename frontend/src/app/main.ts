import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from '@/App.vue'
import { router } from '@/app/router'
import { provideDependencies } from '@/app/dependencies'
import '@/app/styles/main.css'

const app = createApp(App)
provideDependencies(app)
app.use(createPinia()).use(router).mount('#app')

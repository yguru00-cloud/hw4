import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  // BACKEND_URL lets the dev proxy point at a FastAPI server on another port.
  const backend = loadEnv(mode, '.', '').BACKEND_URL || 'http://127.0.0.1:8000'

  return {
    plugins: [react()],
    server: {
      proxy: {
        '/api': backend,
        '/media': backend,
      },
    },
  }
})

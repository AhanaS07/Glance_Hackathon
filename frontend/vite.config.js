import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite configuration for the React frontend.
// Dev server runs on :3000 (per CLAUDE.md) and proxies /api -> the FastAPI
// backend on :8000, so the browser makes same-origin requests (no CORS) and
// api.js can use relative /api/... paths.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})

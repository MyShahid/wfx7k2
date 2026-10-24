import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In development, forward /api calls to the FastAPI server on port 8000.
// In production (Vercel / Docker) the API is served from the same domain.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})

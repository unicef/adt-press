import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3001,
    fs: {
      allow: ['..'] // Allow serving files from parent directory
    }
  },
  build: {
    outDir: 'dist',
  },
  resolve: {
    alias: {
      '/output': resolve(__dirname, '../output')
    }
  }
})
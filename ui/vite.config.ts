import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:18890',
      '/health': 'http://localhost:18890'
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
});

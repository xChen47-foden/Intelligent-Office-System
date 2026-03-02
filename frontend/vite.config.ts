import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  css: {
    preprocessorOptions: {
      scss: {
        // 移除全局变量导入，避免与@forward规则冲突
      }
    }
  },
  server: {
    port: 3006,
    host: '0.0.0.0',
    open: true,
    proxy: {
      '/api': {
        target: 'http://localhost:3007',
        changeOrigin: true,
        secure: false
      },
      '/auth': {
        target: 'http://localhost:3007',
        changeOrigin: true,
        secure: false
      },
      '/ws': {
        target: 'ws://localhost:3007',
        ws: true,
        changeOrigin: true
      },
      '/uploads': {
        target: 'http://localhost:3007',
        changeOrigin: true,
        secure: false
      }
    }
  },
  preview: {
    port: 3006,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:3007',
        changeOrigin: true,
        secure: false
      },
      '/auth': {
        target: 'http://localhost:3007',
        changeOrigin: true,
        secure: false
      },
      '/ws': {
        target: 'ws://localhost:3007',
        ws: true,
        changeOrigin: true
      },
      '/uploads': {
        target: 'http://localhost:3007',
        changeOrigin: true,
        secure: false
      }
    }
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@styles': resolve(__dirname, 'src/assets/styles'),
      '@icons': resolve(__dirname, 'src/assets/icons'),
      '@imgs': resolve(__dirname, 'src/assets/images'),
      '@views': resolve(__dirname, 'src/views'),
      '@utils': resolve(__dirname, 'src/utils')
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false
  }
}) 
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import { fileURLToPath } from 'url'

export default ({ mode }) => {
  const root = process.cwd()
  const env = loadEnv(mode, root)
  const { VITE_VERSION, VITE_PORT, VITE_BASE_URL, VITE_API_URL } = env

  console.log(`🚀 API_URL = ${VITE_API_URL}`)
  console.log(`🚀 VERSION = ${VITE_VERSION}`)

  return defineConfig({
    define: {
      __APP_VERSION__: JSON.stringify(VITE_VERSION)
    },
    base: VITE_BASE_URL,
    server: {
      port: 3006,
      proxy: {
        '/api': {
          target: 'http://localhost:3007',
          changeOrigin: true,
          rewrite: path => path.replace(/^\/api/, '/api')
        },
        '/auth': {
          target: 'http://localhost:3007',
          changeOrigin: true,
        },
        '/uploads': {
          target: 'http://localhost:3007',
          changeOrigin: true,
        }
      },
      host: true
    },
    // 路径别名
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
        '@views': resolvePath('src/views'),
        '@comps': resolvePath('src/components'),
        '@imgs': resolvePath('src/assets/img'),
        '@icons': resolvePath('src/assets/icons'),
        '@utils': resolvePath('src/utils'),
        '@stores': resolvePath('src/store'),
        '@plugins': resolvePath('src/plugins'),
        '@styles': resolvePath('src/assets/styles')
      }
    },
    build: {
      target: 'es2015',
      outDir: 'dist',
      chunkSizeWarningLimit: 2000,
      minify: false, // 暂时禁用压缩避免问题
      rollupOptions: {
        external: ['sqlite3', 'fs', 'path', 'os', 'electron'],
        output: {
          manualChunks: {
            vendor: ['vue', 'vue-router', 'pinia', 'element-plus']
          }
        }
      }
    },
    plugins: [
      vue()
      // 暂时只使用基本的Vue插件，避免复杂配置导致的问题
    ],
    // 预加载项目必需的组件
    optimizeDeps: {
      include: [
        'vue',
        'vue-router',
        'pinia',
        'axios',
        'element-plus'
      ]
    },
    css: {
      preprocessorOptions: {
        // sass variable and mixin
        scss: {
          api: 'modern-compiler',
          additionalData: `
            @use "@styles/variables.scss" as *; @use "@styles/mixin.scss" as *;
          `
        }
      }
    }
  })
}

function resolvePath(paths) {
  const currentDirectory = fileURLToPath(new URL('.', import.meta.url))
  return path.resolve(currentDirectory, paths)
}

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import fs from 'fs'
import path from 'path'

export default defineConfig(({ mode }) => {
  if (mode === 'test') {
    return {
      plugins: [vue()],
      test: {
        environment: 'jsdom',
        globals: true,
      },
    }
  }
  const env = loadEnv(mode, process.cwd(), '')
  const backendPort = env.VITE_BACKEND_PORT || '8000'

  // 证书路径：项目根目录/certs/
  const projectRoot = path.resolve(__dirname, '..', '..', '..', '..')
  const certPath = path.join(projectRoot, 'certs', 'cert.pem')
  const keyPath = path.join(projectRoot, 'certs', 'key.pem')

  const hasCerts = fs.existsSync(certPath) && fs.existsSync(keyPath)

  return {
    plugins: [
      vue(),
      AutoImport({
        resolvers: [ElementPlusResolver()]
      }),
      Components({
        resolvers: [ElementPlusResolver()]
      })
    ],
    css: {
      preprocessorOptions: {
        scss: {
          api: 'modern-compiler'
        }
      }
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            'element-plus': ['element-plus'],
            'echarts': ['echarts'],
            'vue-vendor': ['vue', 'vue-router', 'pinia']
          }
        }
      }
    },
    server: {
      https: hasCerts
        ? {
            cert: fs.readFileSync(certPath),
            key: fs.readFileSync(keyPath),
          }
        : undefined,
      proxy: {
        '/api': {
          target: `https://127.0.0.1:${backendPort}`,
          changeOrigin: true,
          secure: false, // 信任自签名证书
        },
        '/ws': {
          target: `wss://127.0.0.1:${backendPort}`,
          ws: true,
          secure: false,
          configure: (proxy) => {
            proxy.on('error', () => {})
            proxy.on('close', () => {})
          }
        }
      }
    }
  }
})

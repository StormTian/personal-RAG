import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  
  return {
    plugins: [
      react(),
      mode === 'analyze' && visualizer({ open: true }),
    ],
    resolve: {
      alias: {
        '@': '/src',
      },
    },
    server: {
      port: 5173,
      host: true,
      proxy: {
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
          changeOrigin: true,
          rewrite: (path) => path,
        },
      },
    },
    build: {
      target: 'es2020',
      minify: 'terser',
      cssMinify: true,
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom', 'react-router-dom'],
            ui: ['antd', '@ant-design/icons'],
            query: ['@tanstack/react-query'],
            state: ['zustand'],
            i18n: ['i18next', 'react-i18next'],
          },
        },
      },
      chunkSizeWarningLimit: 500,
    },
    css: {
      preprocessorOptions: {
        less: {
          javascriptEnabled: true,
          modifyVars: {},
        },
      },
    },
  };
});

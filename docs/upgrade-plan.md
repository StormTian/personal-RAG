# RAG Demo 前端升级计划

> **For agentic workers:** 使用 React 18 + TypeScript + Vite + Ant Design 技术栈进行全面重构

**目标:** 将现有的原生 HTML/JS 前端升级为生产级别的现代化应用

**架构:** 基于 React 18 + TypeScript + Vite 构建，使用 Ant Design 5.x 作为 UI 组件库，支持暗黑模式、国际化、代码分割等生产级特性

**技术栈:** React 18, TypeScript 5.x, Vite 5.x, Ant Design 5.x, React Query, Zustand, React Router, i18next, PrismJS, dayjs

---

## 项目结构

```
web-new/
├── package.json              # 依赖管理
├── tsconfig.json             # TypeScript 配置
├── vite.config.ts            # Vite 构建配置
├── index.html                # 入口 HTML
├── .env                      # 环境变量
├── .env.production           # 生产环境变量
├── README.md                 # 项目文档
├── public/                   # 静态资源
│   └── favicon.ico
├── src/
│   ├── main.tsx              # 应用入口
│   ├── App.tsx               # 根组件
│   ├── vite-env.d.ts         # Vite 类型声明
│   ├── components/           # 公共组件
│   │   ├── ErrorBoundary/
│   │   ├── Loading/
│   │   ├── Skeleton/
│   │   └── ThemeToggle/
│   ├── features/             # 功能模块
│   │   ├── search/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── stores/
│   │   │   └── types/
│   │   ├── library/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   └── types/
│   │   └── result/
│   │       ├── components/
│   │       ├── hooks/
│   │       └── types/
│   ├── hooks/                # 全局 Hooks
│   ├── i18n/                 # 国际化配置
│   │   ├── index.ts
│   │   ├── locales/
│   │   │   ├── zh-CN.json
│   │   │   └── en-US.json
│   │   └── config.ts
│   ├── layouts/              # 布局组件
│   │   └── MainLayout/
│   ├── pages/                # 页面组件
│   │   └── Home/
│   ├── services/             # API 服务
│   │   ├── api.ts
│   │   ├── types.ts
│   │   └── client.ts
│   ├── stores/               # 全局状态
│   │   └── themeStore.ts
│   ├── styles/               # 全局样式
│   │   ├── global.less
│   │   ├── variables.less
│   │   └── theme.ts
│   ├── types/                # 全局类型
│   │   └── index.ts
│   └── utils/                # 工具函数
│       ├── highlight.ts
│       ├── storage.ts
│       └── format.ts
└── tests/                    # 测试文件
    ├── unit/
    └── e2e/
```

---

## 任务清单

### Phase 1: 项目初始化

#### Task 1: 创建基础项目结构

**文件:**
- 创建: `web-new/package.json`
- 创建: `web-new/tsconfig.json`
- 创建: `web-new/vite.config.ts`
- 创建: `web-new/index.html`
- 创建: `web-new/.gitignore`

**步骤:**

- [ ] **步骤 1: 创建 package.json**

```json
{
  "name": "rag-demo-web",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --host",
    "build": "tsc && vite build",
    "build:analyze": "tsc && vite build --mode analyze",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "lint:fix": "eslint . --ext ts,tsx --fix",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:ui": "vitest --ui",
    "coverage": "vitest run --coverage"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0",
    "antd": "^5.12.0",
    "@ant-design/icons": "^5.2.6",
    "@tanstack/react-query": "^5.13.0",
    "zustand": "^4.4.7",
    "i18next": "^23.7.0",
    "react-i18next": "^13.5.0",
    "i18next-browser-languagedetector": "^7.2.0",
    "prismjs": "^1.29.0",
    "dayjs": "^1.11.10",
    "lodash-es": "^4.17.21",
    "axios": "^1.6.2"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@types/prismjs": "^1.26.3",
    "@types/lodash-es": "^4.17.12",
    "@typescript-eslint/eslint-plugin": "^6.14.0",
    "@typescript-eslint/parser": "^6.14.0",
    "@vitejs/plugin-react": "^4.2.1",
    "eslint": "^8.55.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "typescript": "^5.3.3",
    "vite": "^5.0.8",
    "vite-plugin-pwa": "^0.17.4",
    "rollup-plugin-visualizer": "^5.11.0",
    "@rollup/plugin-replace": "^5.0.5",
    "vitest": "^1.1.0",
    "@vitest/ui": "^1.1.0",
    "@vitest/coverage-v8": "^1.1.0",
    "less": "^4.2.0",
    "postcss": "^8.4.32",
    "autoprefixer": "^10.4.16",
    "tailwindcss": "^3.3.6",
    "eslint-config-prettier": "^9.1.0",
    "prettier": "^3.1.1"
  }
}
```

- [ ] **步骤 2: 创建 tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **步骤 3: 创建 vite.config.ts**

```typescript
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
      port: 3000,
      proxy: {
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://localhost:8000',
          changeOrigin: true,
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
```

- [ ] **步骤 4: 创建 index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="Tiny RAG Demo - 本地可跑的 RAG 小实验室" />
    <meta name="theme-color" content="#99582a" />
    <title>Tiny RAG Demo</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **步骤 5: 安装依赖**

```bash
cd web-new && npm install
```

---

### Phase 2: 核心配置

#### Task 2: 配置 TypeScript 和路径别名

**文件:**
- 创建: `web-new/tsconfig.node.json`
- 创建: `web-new/src/vite-env.d.ts`

**步骤:**

- [ ] **步骤 1: 创建 tsconfig.node.json**

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true,
    "strict": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **步骤 2: 创建 vite-env.d.ts**

```typescript
/// <reference types="vite/client" />

declare module '*.svg' {
  const content: React.FunctionComponent<React.SVGProps<SVGSVGElement>>;
  export default content;
}

declare module '*.png' {
  const content: string;
  export default content;
}

declare module '*.jpg' {
  const content: string;
  export default content;
}

declare module '*.less' {
  const content: { [className: string]: string };
  export default content;
}
```

---

### Phase 3: 全局类型和工具函数

#### Task 3: 创建全局类型定义

**文件:**
- 创建: `web-new/src/types/index.ts`
- 创建: `web-new/src/utils/format.ts`
- 创建: `web-new/src/utils/storage.ts`

**步骤:**

- [ ] **步骤 1: 创建 types/index.ts**

```typescript
// API 响应类型
export interface ApiResponse<T = unknown> {
  data: T;
  success: boolean;
  message?: string;
}

export interface ApiError {
  error: string;
  code?: number;
}

// 文档库类型
export interface LibraryInfo {
  documents: number;
  chunks: number;
  supported_formats: string[];
  embedding_backend: string;
  reranker_backend: string;
  retrieval_strategy: string;
  rerank_strategy: string;
  files: LibraryFile[];
  skipped: SkippedFile[];
}

export interface LibraryFile {
  source: string;
  title: string;
  file_type: string;
  chars: number;
}

export interface SkippedFile {
  source: string;
  error: string;
}

// 搜索结果类型
export interface SearchHit {
  source: string;
  text: string;
  score: number;
  retrieve_score: number;
  lexical_score: number;
}

export interface SearchResponse {
  answer_lines: string[];
  hits: SearchHit[];
  query_time?: number;
}

export interface SearchParams {
  query: string;
  top_k: number;
}

// 主题类型
export type ThemeMode = 'light' | 'dark' | 'system';

// 搜索历史
export interface SearchHistoryItem {
  id: string;
  query: string;
  timestamp: number;
  hitCount: number;
}
```

- [ ] **步骤 2: 创建 utils/format.ts**

```typescript
export function formatScore(score: number): string {
  return score.toFixed(3);
}

export function formatDate(timestamp: number): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  
  if (minutes < 1) return '刚刚';
  if (minutes < 60) return `${minutes}分钟前`;
  if (hours < 24) return `${hours}小时前`;
  if (days < 30) return `${days}天前`;
  
  return date.toLocaleDateString('zh-CN');
}

export function escapeHtml(str: string): string {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

export function highlightText(text: string, keywords: string[]): string {
  if (!keywords.length) return text;
  
  const regex = new RegExp(
    `(${keywords.map(k => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`,
    'gi'
  );
  
  return text.replace(regex, '<mark class="highlight-text">$1</mark>');
}
```

- [ ] **步骤 3: 创建 utils/storage.ts**

```typescript
const STORAGE_PREFIX = 'rag_demo_';

export const storage = {
  get<T>(key: string, defaultValue?: T): T | undefined {
    try {
      const item = localStorage.getItem(`${STORAGE_PREFIX}${key}`);
      return item ? JSON.parse(item) : defaultValue;
    } catch {
      return defaultValue;
    }
  },
  
  set<T>(key: string, value: T): void {
    try {
      localStorage.setItem(`${STORAGE_PREFIX}${key}`, JSON.stringify(value));
    } catch {
      console.warn('localStorage set failed');
    }
  },
  
  remove(key: string): void {
    localStorage.removeItem(`${STORAGE_PREFIX}${key}`);
  },
  
  clear(): void {
    Object.keys(localStorage)
      .filter(key => key.startsWith(STORAGE_PREFIX))
      .forEach(key => localStorage.removeItem(key));
  },
};
```

---

### Phase 4: 服务层

#### Task 4: 创建 API 服务层

**文件:**
- 创建: `web-new/src/services/client.ts`
- 创建: `web-new/src/services/types.ts`
- 创建: `web-new/src/services/api.ts`

**步骤:**

- [ ] **步骤 1: 创建 services/client.ts**

```typescript
import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;
  
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    this.setupInterceptors();
  }
  
  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if needed
        return config;
      },
      (error) => Promise.reject(error)
    );
    
    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response.data,
      (error: AxiosError<{ error?: string }>) => {
        const message = error.response?.data?.error || error.message || '请求失败';
        return Promise.reject(new Error(message));
      }
    );
  }
  
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.client.get(url, config);
  }
  
  async post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return this.client.post(url, data, config);
  }
  
  async put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return this.client.put(url, data, config);
  }
  
  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.client.delete(url, config);
  }
}

export const apiClient = new ApiClient();
```

- [ ] **步骤 2: 创建 services/api.ts**

```typescript
import { apiClient } from './client';
import type {
  LibraryInfo,
  SearchResponse,
  SearchParams,
} from '@/types';

export const libraryApi = {
  async getInfo(): Promise<LibraryInfo> {
    return apiClient.get<LibraryInfo>('/api/library');
  },
  
  async reload(): Promise<LibraryInfo> {
    return apiClient.post<LibraryInfo>('/api/reload');
  },
};

export const searchApi = {
  async query(params: SearchParams): Promise<SearchResponse> {
    return apiClient.post<SearchResponse>('/api/ask', params);
  },
};
```

---

### Phase 5: 国际化配置

#### Task 5: 配置 i18n

**文件:**
- 创建: `web-new/src/i18n/config.ts`
- 创建: `web-new/src/i18n/index.ts`
- 创建: `web-new/src/i18n/locales/zh-CN.json`
- 创建: `web-new/src/i18n/locales/en-US.json`

**步骤:**

- [ ] **步骤 1: 创建 i18n/config.ts**

```typescript
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import zhCN from './locales/zh-CN.json';
import enUS from './locales/en-US.json';

export const resources = {
  'zh-CN': { translation: zhCN },
  'en-US': { translation: enUS },
};

export const defaultNS = 'translation';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'zh-CN',
    defaultNS,
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
    },
  });

export default i18n;
```

- [ ] **步骤 2: 创建 i18n/locales/zh-CN.json**

```json
{
  "app": {
    "title": "Tiny RAG Demo",
    "subtitle": "本地可跑的 RAG 小实验室",
    "description": "输入一个问题，页面会展示离线检索生成的答案，以及命中的知识片段。"
  },
  "search": {
    "title": "提问",
    "badge": "TF-IDF + Chunk Retrieval",
    "placeholder": "输入你想问文档库的问题",
    "button": "开始检索",
    "buttonLoading": "检索中...",
    "recallCount": "召回条数",
    "noResults": "没有命中上下文",
    "noAnswer": "没有生成回答",
    "history": "搜索历史",
    "clearHistory": "清空历史",
    "hitCount": "命中 {count} 条上下文"
  },
  "library": {
    "title": "文档库",
    "description": "已入库 {documents} 个文档，切分为 {chunks} 个 chunk",
    "formats": "支持格式",
    "embedding": "Embedding",
    "reranker": "Reranker",
    "retrieval": "检索链路",
    "reload": "重新入库",
    "empty": "文档库里还没有可入库的文件",
    "skipped": "跳过 {count} 个文件"
  },
  "result": {
    "title": "回答与上下文",
    "answer": "回答",
    "contexts": "命中的文档片段",
    "score": "Score",
    "vectorScore": "Vec",
    "bm25Score": "BM25"
  },
  "status": {
    "waiting": "等待提问",
    "loading": "正在检索",
    "success": "检索完成",
    "error": "请求失败",
    "reloadSuccess": "重新入库完成",
    "reloadError": "重新入库失败"
  },
  "error": {
    "emptyQuery": "请输入问题",
    "loadLibrary": "读取文档库失败",
    "unknown": "发生未知错误",
    "retry": "重试"
  },
  "theme": {
    "light": "浅色模式",
    "dark": "深色模式",
    "system": "跟随系统"
  }
}
```

- [ ] **步骤 3: 创建 i18n/locales/en-US.json**

```json
{
  "app": {
    "title": "Tiny RAG Demo",
    "subtitle": "Local RAG Laboratory",
    "description": "Enter a question to see offline retrieval-generated answers and matched knowledge snippets."
  },
  "search": {
    "title": "Ask",
    "badge": "TF-IDF + Chunk Retrieval",
    "placeholder": "Enter your question for the document library",
    "button": "Start Search",
    "buttonLoading": "Searching...",
    "recallCount": "Recall Count",
    "noResults": "No context matches found",
    "noAnswer": "No answer generated",
    "history": "Search History",
    "clearHistory": "Clear History",
    "hitCount": "Found {count} context matches"
  },
  "library": {
    "title": "Document Library",
    "description": "{documents} documents indexed, split into {chunks} chunks",
    "formats": "Supported Formats",
    "embedding": "Embedding",
    "reranker": "Reranker",
    "retrieval": "Retrieval Pipeline",
    "reload": "Reload Library",
    "empty": "No documents in the library yet",
    "skipped": "Skipped {count} files"
  },
  "result": {
    "title": "Answer & Context",
    "answer": "Answer",
    "contexts": "Matched Document Snippets",
    "score": "Score",
    "vectorScore": "Vec",
    "bm25Score": "BM25"
  },
  "status": {
    "waiting": "Waiting for question",
    "loading": "Searching",
    "success": "Search completed",
    "error": "Request failed",
    "reloadSuccess": "Reload completed",
    "reloadError": "Reload failed"
  },
  "error": {
    "emptyQuery": "Please enter a question",
    "loadLibrary": "Failed to load library",
    "unknown": "Unknown error occurred",
    "retry": "Retry"
  },
  "theme": {
    "light": "Light Mode",
    "dark": "Dark Mode",
    "system": "System"
  }
}
```

---

### Phase 6: 主题和样式配置

#### Task 6: 配置主题系统

**文件:**
- 创建: `web-new/src/stores/themeStore.ts`
- 创建: `web-new/src/styles/theme.ts`
- 创建: `web-new/src/styles/variables.less`
- 创建: `web-new/src/styles/global.less`

**步骤:**

- [ ] **步骤 1: 创建 stores/themeStore.ts**

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ThemeMode } from '@/types';

interface ThemeState {
  mode: ThemeMode;
  isDark: boolean;
  setMode: (mode: ThemeMode) => void;
  toggleMode: () => void;
}

const getIsDark = (mode: ThemeMode): boolean => {
  if (mode === 'system') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  return mode === 'dark';
};

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      mode: 'system',
      isDark: getIsDark('system'),
      
      setMode: (mode) => {
        set({ mode, isDark: getIsDark(mode) });
      },
      
      toggleMode: () => {
        const currentMode = get().mode;
        const newMode: ThemeMode = currentMode === 'dark' ? 'light' : 'dark';
        set({ mode: newMode, isDark: getIsDark(newMode) });
      },
    }),
    {
      name: 'theme-storage',
      onRehydrateStorage: () => (state) => {
        if (state) {
          state.isDark = getIsDark(state.mode);
        }
      },
    }
  )
);

// Listen for system theme changes
if (typeof window !== 'undefined') {
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    const state = useThemeStore.getState();
    if (state.mode === 'system') {
      useThemeStore.setState({ isDark: e.matches });
    }
  });
}
```

- [ ] **步骤 2: 创建 styles/theme.ts**

```typescript
import type { ThemeConfig } from 'antd';

export const lightTheme: ThemeConfig = {
  token: {
    colorPrimary: '#99582a',
    colorBgBase: '#f5efe6',
    colorTextBase: '#1f1a17',
    colorBorder: 'rgba(95, 72, 47, 0.18)',
    borderRadius: 12,
    fontFamily: '"Avenir Next", "Trebuchet MS", -apple-system, BlinkMacSystemFont, sans-serif',
  },
  components: {
    Button: {
      borderRadius: 999,
    },
    Card: {
      borderRadius: 18,
    },
    Input: {
      borderRadius: 18,
    },
  },
};

export const darkTheme: ThemeConfig = {
  token: {
    colorPrimary: '#c97d60',
    colorBgBase: '#1a1614',
    colorTextBase: '#e8e4e0',
    colorBorder: 'rgba(255, 255, 255, 0.12)',
    borderRadius: 12,
    fontFamily: '"Avenir Next", "Trebuchet MS", -apple-system, BlinkMacSystemFont, sans-serif',
  },
  components: {
    Button: {
      borderRadius: 999,
    },
    Card: {
      borderRadius: 18,
      colorBgContainer: '#2a2522',
    },
    Input: {
      borderRadius: 18,
      colorBgContainer: '#2a2522',
    },
  },
};
```

- [ ] **步骤 3: 创建 styles/global.less**

```less
// Global styles
* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  min-height: 100vh;
  font-family: "Avenir Next", "Trebuchet MS", -apple-system, BlinkMacSystemFont, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

// Highlight text
.highlight-text {
  background-color: rgba(201, 125, 96, 0.3);
  padding: 0 2px;
  border-radius: 2px;
}

// Custom scrollbar
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}

// Focus visible
:focus-visible {
  outline: 2px solid var(--ant-color-primary);
  outline-offset: 2px;
}

// Markdown styles
.markdown-body {
  line-height: 1.7;
  
  pre {
    background: #f6f8fa;
    padding: 16px;
    border-radius: 8px;
    overflow-x: auto;
    
    code {
      background: transparent;
      padding: 0;
    }
  }
  
  code {
    background: rgba(175, 184, 193, 0.2);
    padding: 0.2em 0.4em;
    border-radius: 6px;
    font-size: 85%;
  }
  
  h1, h2, h3, h4, h5, h6 {
    margin-top: 24px;
    margin-bottom: 16px;
    font-weight: 600;
    line-height: 1.25;
  }
}

// Dark mode adjustments
.dark {
  .markdown-body {
    pre {
      background: #2d333b;
    }
    
    code {
      background: rgba(99, 110, 123, 0.4);
    }
  }
  
  ::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
  }
  
  ::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.3);
  }
}
```

---

### Phase 7: 布局组件

#### Task 7: 创建布局组件

**文件:**
- 创建: `web-new/src/components/ThemeToggle/ThemeToggle.tsx`
- 创建: `web-new/src/components/ErrorBoundary/ErrorBoundary.tsx`
- 创建: `web-new/src/layouts/MainLayout/MainLayout.tsx`

**步骤:**

- [ ] **步骤 1: 创建 ThemeToggle 组件**

```typescript
import React from 'react';
import { Button, Tooltip } from 'antd';
import { MoonOutlined, SunOutlined } from '@ant-design/icons';
import { useThemeStore } from '@/stores/themeStore';
import { useTranslation } from 'react-i18next';

export const ThemeToggle: React.FC = () => {
  const { isDark, toggleMode } = useThemeStore();
  const { t } = useTranslation();
  
  return (
    <Tooltip title={t(isDark ? 'theme.light' : 'theme.dark')}>
      <Button
        type="text"
        icon={isDark ? <SunOutlined /> : <MoonOutlined />}
        onClick={toggleMode}
        aria-label={t(isDark ? 'theme.light' : 'theme.dark')}
      />
    </Tooltip>
  );
};
```

- [ ] **步骤 2: 创建 ErrorBoundary 组件**

```typescript
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Result, Button } from 'antd';
import { useTranslation } from 'react-i18next';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundaryClass extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }
  
  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }
  
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }
  
  handleReset = () => {
    this.setState({ hasError: false, error: undefined });
    window.location.reload();
  };
  
  render() {
    if (this.state.hasError) {
      return (
        <Result
          status="error"
          title="Something went wrong"
          subTitle={this.state.error?.message}
          extra={[
            <Button type="primary" key="reset" onClick={this.handleReset}>
              Reload Page
            </Button>,
          ]}
        />
      );
    }
    
    return this.props.children;
  }
}

export const ErrorBoundary: React.FC<{ children: ReactNode }> = ({ children }) => {
  return <ErrorBoundaryClass>{children}</ErrorBoundaryClass>;
};
```

- [ ] **步骤 3: 创建 MainLayout**

```typescript
import React from 'react';
import { Layout, ConfigProvider, theme as antTheme } from 'antd';
import { ThemeToggle } from '@/components/ThemeToggle/ThemeToggle';
import { useThemeStore } from '@/stores/themeStore';
import { lightTheme, darkTheme } from '@/styles/theme';

const { Header, Content } = Layout;

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const { isDark } = useThemeStore();
  
  return (
    <ConfigProvider
      theme={{
        algorithm: isDark ? antTheme.darkAlgorithm : antTheme.defaultAlgorithm,
        ...isDark ? darkTheme : lightTheme,
      }}
    >
      <div className={isDark ? 'dark' : 'light'}>
        <Layout style={{ minHeight: '100vh' }}>
          <Header
            style={{
              display: 'flex',
              justifyContent: 'flex-end',
              alignItems: 'center',
              padding: '0 24px',
              background: 'transparent',
            }}
          >
            <ThemeToggle />
          </Header>
          <Content style={{ padding: '0 24px 48px' }}>
            {children}
          </Content>
        </Layout>
      </div>
    </ConfigProvider>
  );
};
```

---

### Phase 8: 搜索功能模块

#### Task 8: 创建搜索功能模块

**文件:**
- 创建: `web-new/src/features/search/stores/searchStore.ts`
- 创建: `web-new/src/features/search/components/SearchForm.tsx`
- 创建: `web-new/src/features/search/components/SearchHistory.tsx`
- 创建: `web-new/src/features/search/hooks/useSearch.ts`

**步骤:**

- [ ] **步骤 1: 创建 searchStore.ts**

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { SearchHistoryItem } from '@/types';
import { nanoid } from 'nanoid';

interface SearchState {
  history: SearchHistoryItem[];
  addToHistory: (query: string, hitCount: number) => void;
  clearHistory: () => void;
  removeFromHistory: (id: string) => void;
}

const MAX_HISTORY = 20;

export const useSearchStore = create<SearchState>()(
  persist(
    (set, get) => ({
      history: [],
      
      addToHistory: (query, hitCount) => {
        const { history } = get();
        const newItem: SearchHistoryItem = {
          id: nanoid(),
          query,
          timestamp: Date.now(),
          hitCount,
        };
        
        set({
          history: [newItem, ...history.filter(h => h.query !== query)].slice(0, MAX_HISTORY),
        });
      },
      
      clearHistory: () => set({ history: [] }),
      
      removeFromHistory: (id) => {
        const { history } = get();
        set({ history: history.filter(h => h.id !== id) });
      },
    }),
    {
      name: 'search-history',
    }
  )
);
```

- [ ] **步骤 2: 创建 SearchForm 组件**

```typescript
import React, { useState, useCallback } from 'react';
import { Form, Input, Button, Card, Space, Typography, InputNumber } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface SearchFormProps {
  onSearch: (query: string, topK: number) => void;
  loading?: boolean;
}

export const SearchForm: React.FC<SearchFormProps> = ({ onSearch, loading }) => {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const [query, setQuery] = useState('');
  
  const handleSubmit = useCallback(() => {
    form.validateFields().then(({ query, topK }) => {
      onSearch(query, topK);
    });
  }, [form, onSearch]);
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.metaKey) {
      handleSubmit();
    }
  };
  
  return (
    <Card
      title={
        <Space>
          <Title level={3} style={{ margin: 0 }}>{t('search.title')}</Title>
          <Text type="secondary" style={{ fontSize: 12, background: 'rgba(153, 88, 42, 0.1)', padding: '2px 8px', borderRadius: 999 }}>
            {t('search.badge')}
          </Text>
        </Space>
      }
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{ topK: 3 }}
        onFinish={handleSubmit}
      >
        <Form.Item
          name="query"
          label={t('search.placeholder')}
          rules={[{ required: true, message: t('error.emptyQuery') }]}
        >
          <TextArea
            rows={4}
            placeholder={t('search.placeholder')}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            autoFocus
          />
        </Form.Item>
        
        <Space align="end" style={{ width: '100%', justifyContent: 'space-between' }}>
          <Form.Item
            name="topK"
            label={t('search.recallCount')}
            style={{ marginBottom: 0 }}
          >
            <InputNumber min={1} max={20} />
          </Form.Item>
          
          <Button
            type="primary"
            icon={<SearchOutlined />}
            onClick={handleSubmit}
            loading={loading}
            size="large"
          >
            {loading ? t('search.buttonLoading') : t('search.button')}
          </Button>
        </Space>
      </Form>
    </Card>
  );
};
```

- [ ] **步骤 3: 创建 SearchHistory 组件**

```typescript
import React from 'react';
import { Card, List, Tag, Space, Typography, Button, Empty } from 'antd';
import { ClockCircleOutlined, DeleteOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useSearchStore } from '../stores/searchStore';
import { formatDate } from '@/utils/format';

const { Text } = Typography;

interface SearchHistoryProps {
  onSelect: (query: string) => void;
}

export const SearchHistory: React.FC<SearchHistoryProps> = ({ onSelect }) => {
  const { t } = useTranslation();
  const { history, removeFromHistory, clearHistory } = useSearchStore();
  
  if (history.length === 0) {
    return null;
  }
  
  return (
    <Card
      title={
        <Space>
          <ClockCircleOutlined />
          {t('search.history')}
        </Space>
      }
      extra={
        <Button type="link" onClick={clearHistory}>
          {t('search.clearHistory')}
        </Button>
      }
      style={{ marginTop: 24 }}
    >
      <List
        dataSource={history}
        renderItem={(item) => (
          <List.Item
            actions={[
              <Button
                type="text"
                icon={<DeleteOutlined />}
                onClick={() => removeFromHistory(item.id)}
                aria-label="Remove"
              />,
            ]}
          >
            <Space direction="vertical" size={0} style={{ width: '100%' }}>
              <Text
                strong
                style={{ cursor: 'pointer' }}
                onClick={() => onSelect(item.query)}
              >
                {item.query}
              </Text>
              <Space>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {formatDate(item.timestamp)}
                </Text>
                <Tag size="small">{item.hitCount} hits</Tag>
              </Space>
            </Space>
          </List.Item>
        )}
      />
    </Card>
  );
};
```

---

### Phase 9: 文档库模块

#### Task 9: 创建文档库模块

**文件:**
- 创建: `web-new/src/features/library/components/LibraryPanel.tsx`
- 创建: `web-new/src/features/library/hooks/useLibrary.ts`

**步骤:**

- [ ] **步骤 1: 创建 LibraryPanel 组件**

```typescript
import React from 'react';
import { Card, List, Typography, Tag, Space, Button, Skeleton, Alert } from 'antd';
import { ReloadOutlined, FileTextOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import type { LibraryInfo } from '@/types';

const { Title, Text, Paragraph } = Typography;

interface LibraryPanelProps {
  data?: LibraryInfo;
  loading?: boolean;
  error?: Error | null;
  onReload: () => void;
}

export const LibraryPanel: React.FC<LibraryPanelProps> = ({
  data,
  loading,
  error,
  onReload,
}) => {
  const { t } = useTranslation();
  
  if (loading) {
    return (
      <Card title={t('library.title')}>
        <Skeleton active paragraph={{ rows: 4 }} />
      </Card>
    );
  }
  
  if (error) {
    return (
      <Card title={t('library.title')}>
        <Alert
          message={error.message}
          type="error"
          action={
            <Button onClick={onReload} icon={<ReloadOutlined />}>
              {t('error.retry')}
            </Button>
          }
        />
      </Card>
    );
  }
  
  if (!data) {
    return null;
  }
  
  return (
    <Card
      title={<Title level={3} style={{ margin: 0 }}>{t('library.title')}</Title>}
      extra={
        <Button icon={<ReloadOutlined />} onClick={onReload}>
          {t('library.reload')}
        </Button>
      }
    >
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Paragraph>
          {t('library.description', {
            documents: data.documents,
            chunks: data.chunks,
          })}
        </Paragraph>
        
        <Space wrap>
          <Tag color="blue">{t('library.embedding')}: {data.embedding_backend}</Tag>
          <Tag color="green">{t('library.reranker')}: {data.reranker_backend}</Tag>
        </Space>
        
        <div>
          <Text type="secondary">{t('library.formats')}: </Text>
          <Text>{data.supported_formats.join(', ')}</Text>
        </div>
        
        <div>
          <Text type="secondary">{t('library.retrieval')}: </Text>
          <Text>{data.retrieval_strategy} → {data.rerank_strategy}</Text>
        </div>
        
        <List
          header={<Text strong>已入库文件</Text>}
          dataSource={data.files}
          renderItem={(file) => (
            <List.Item>
              <List.Item.Meta
                avatar={<FileTextOutlined />}
                title={file.source}
                description={`${file.title} | ${file.file_type} | ${file.chars} 字符`}
              />
            </List.Item>
          )}
          locale={{ emptyText: t('library.empty') }}
        />
        
        {data.skipped.length > 0 && (
          <Alert
            message={t('library.skipped', { count: data.skipped.length })}
            description={data.skipped.map(s => `${s.source}: ${s.error}`).join('; ')}
            type="warning"
            showIcon
          />
        )}
      </Space>
    </Card>
  );
};
```

---

### Phase 10: 搜索结果模块

#### Task 10: 创建结果展示模块

**文件:**
- 创建: `web-new/src/features/result/components/ResultPanel.tsx`
- 创建: `web-new/src/features/result/components/AnswerCard.tsx`
- 创建: `web-new/src/features/result/components/ContextCard.tsx`
- 创建: `web-new/src/utils/highlight.ts`

**步骤:**

- [ ] **步骤 1: 创建 highlight.ts**

```typescript
import Prism from 'prismjs';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-typescript';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-markdown';

export function highlightCode(code: string, language: string): string {
  try {
    const grammar = Prism.languages[language] || Prism.languages.markup;
    return Prism.highlight(code, grammar, language);
  } catch {
    return code;
  }
}

export function processMarkdown(content: string): string {
  // Process code blocks
  let processed = content.replace(
    /```(\w+)?\n([\s\S]*?)```/g,
    (match, lang, code) => {
      const language = lang || 'text';
      const highlighted = highlightCode(code.trim(), language);
      return `<pre class="language-${language}"><code class="language-${language}">${highlighted}</code></pre>`;
    }
  );
  
  // Process inline code
  processed = processed.replace(
    /`([^`]+)`/g,
    '<code>$1</code>'
  );
  
  return processed;
}
```

- [ ] **步骤 2: 创建 AnswerCard 组件**

```typescript
import React from 'react';
import { Card, Typography, Skeleton, Empty } from 'antd';
import { useTranslation } from 'react-i18next';
import { processMarkdown } from '@/utils/highlight';
import './AnswerCard.less';

const { Title } = Typography;

interface AnswerCardProps {
  lines: string[];
  loading?: boolean;
}

export const AnswerCard: React.FC<AnswerCardProps> = ({ lines, loading }) => {
  const { t } = useTranslation();
  
  if (loading) {
    return (
      <Card title={t('result.answer')}>
        <Skeleton active paragraph={{ rows: 6 }} />
      </Card>
    );
  }
  
  if (!lines.length) {
    return (
      <Card title={t('result.answer')}>
        <Empty description={t('search.noAnswer')} />
      </Card>
    );
  }
  
  const markdown = lines.join('\n\n');
  const html = processMarkdown(markdown);
  
  return (
    <Card title={<Title level={4}>{t('result.answer')}</Title>}>
      <div
        className="answer-content markdown-body"
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </Card>
  );
};
```

- [ ] **步骤 3: 创建 ContextCard 组件**

```typescript
import React from 'react';
import { Card, Tag, Space, Typography, Tooltip } from 'antd';
import type { SearchHit } from '@/types';
import { formatScore, highlightText } from '@/utils/format';
import { useTranslation } from 'react-i18next';

const { Text } = Typography;

interface ContextCardProps {
  hit: SearchHit;
  keywords?: string[];
}

export const ContextCard: React.FC<ContextCardProps> = ({ hit, keywords }) => {
  const { t } = useTranslation();
  const highlightedText = keywords?.length
    ? highlightText(hit.text, keywords)
    : hit.text;
  
  return (
    <Card
      size="small"
      title={
        <Space>
          <Text strong>{hit.source}</Text>
          <Tooltip title={`Vector: ${formatScore(hit.retrieve_score)}, BM25: ${formatScore(hit.lexical_score)}`}>
            <Tag color="blue">
              {t('result.score')} {formatScore(hit.score)}
            </Tag>
          </Tooltip>
        </Space>
      }
    >
      <div
        dangerouslySetInnerHTML={{ __html: highlightedText }}
        style={{ lineHeight: 1.7 }}
      />
    </Card>
  );
};
```

- [ ] **步骤 4: 创建 ResultPanel 组件**

```typescript
import React, { useMemo } from 'react';
import { Card, Space, Typography, Tag, Skeleton, Empty, Alert } from 'antd';
import { useTranslation } from 'react-i18next';
import type { SearchResponse, SearchParams } from '@/types';
import { AnswerCard } from './AnswerCard';
import { ContextCard } from './ContextCard';

const { Title } = Typography;

interface ResultPanelProps {
  data?: SearchResponse;
  loading?: boolean;
  error?: Error | null;
  query?: string;
  onRetry?: () => void;
}

export const ResultPanel: React.FC<ResultPanelProps> = ({
  data,
  loading,
  error,
  query,
  onRetry,
}) => {
  const { t } = useTranslation();
  
  const keywords = useMemo(() => {
    if (!query) return [];
    return query.split(/\s+/).filter(w => w.length > 1);
  }, [query]);
  
  if (loading) {
    return (
      <Card title={t('result.title')}>
        <Skeleton active paragraph={{ rows: 8 }} />
      </Card>
    );
  }
  
  if (error) {
    return (
      <Card title={t('result.title')}>
        <Alert
          message={error.message}
          type="error"
          action={onRetry && (
            <button onClick={onRetry}>{t('error.retry')}</button>
          )}
          showIcon
        />
      </Card>
    );
  }
  
  if (!data) {
    return (
      <Card title={t('result.title')}>
        <Empty description={t('status.waiting')} />
      </Card>
    );
  }
  
  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <AnswerCard lines={data.answer_lines} />
      
      <Card title={<Title level={4}>{t('result.contexts')}</Title>}>
        {data.hits.length === 0 ? (
          <Empty description={t('search.noResults')} />
        ) : (
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            {data.hits.map((hit, index) => (
              <ContextCard
                key={`${hit.source}-${index}`}
                hit={hit}
                keywords={keywords}
              />
            ))}
          </Space>
        )}
      </Card>
    </Space>
  );
};
```

---

### Phase 11: 数据获取 Hooks

#### Task 11: 创建 React Query Hooks

**文件:**
- 创建: `web-new/src/hooks/useLibraryQuery.ts`
- 创建: `web-new/src/hooks/useSearchQuery.ts`
- 创建: `web-new/src/hooks/useReloadMutation.ts`

**步骤:**

- [ ] **步骤 1: 创建 useLibraryQuery.ts**

```typescript
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { libraryApi } from '@/services/api';

const LIBRARY_QUERY_KEY = 'library';

export function useLibraryQuery() {
  return useQuery({
    queryKey: [LIBRARY_QUERY_KEY],
    queryFn: () => libraryApi.getInfo(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
}

export function useLibraryInvalidation() {
  const queryClient = useQueryClient();
  
  return {
    invalidate: () => {
      queryClient.invalidateQueries({ queryKey: [LIBRARY_QUERY_KEY] });
    },
  };
}
```

- [ ] **步骤 2: 创建 useSearchQuery.ts**

```typescript
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { searchApi } from '@/services/api';
import type { SearchParams } from '@/types';

const SEARCH_QUERY_KEY = 'search';

export function useSearchQuery(params: SearchParams | null) {
  return useQuery({
    queryKey: [SEARCH_QUERY_KEY, params],
    queryFn: () => {
      if (!params) throw new Error('No search params');
      return searchApi.query(params);
    },
    enabled: !!params?.query,
    staleTime: 0,
    gcTime: 10 * 60 * 1000, // 10 minutes
  });
}
```

- [ ] **步骤 3: 创建 useReloadMutation.ts**

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { libraryApi } from '@/services/api';

export function useReloadMutation() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => libraryApi.reload(),
    onSuccess: (data) => {
      queryClient.setQueryData(['library'], data);
    },
  });
}
```

---

### Phase 12: 主页面

#### Task 12: 创建主页面

**文件:**
- 创建: `web-new/src/pages/Home/Home.tsx`
- 创建: `web-new/src/App.tsx`
- 创建: `web-new/src/main.tsx`

**步骤:**

- [ ] **步骤 1: 创建 Home 页面**

```typescript
import React, { useState, useCallback } from 'react';
import { Row, Col, Typography, Tag, Space, message } from 'antd';
import { useTranslation } from 'react-i18next';
import { SearchForm } from '@/features/search/components/SearchForm';
import { SearchHistory } from '@/features/search/components/SearchHistory';
import { LibraryPanel } from '@/features/library/components/LibraryPanel';
import { ResultPanel } from '@/features/result/components/ResultPanel';
import { useLibraryQuery } from '@/hooks/useLibraryQuery';
import { useReloadMutation } from '@/hooks/useReloadMutation';
import { useSearchStore } from '@/features/search/stores/searchStore';
import { searchApi } from '@/services/api';
import type { SearchParams, SearchResponse } from '@/types';

const { Title, Paragraph } = Typography;

export const Home: React.FC = () => {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useState<SearchParams | null>(null);
  const [searchResult, setSearchResult] = useState<SearchResponse | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<Error | null>(null);
  
  const { data: libraryData, isLoading: isLibraryLoading, error: libraryError, refetch: refetchLibrary } = useLibraryQuery();
  const { mutate: reloadLibrary, isPending: isReloading } = useReloadMutation();
  const { addToHistory } = useSearchStore();
  
  const handleSearch = useCallback(async (query: string, topK: number) => {
    setIsSearching(true);
    setSearchError(null);
    setSearchParams({ query, top_k: topK });
    
    try {
      const result = await searchApi.query({ query, top_k: topK });
      setSearchResult(result);
      addToHistory(query, result.hits.length);
    } catch (err) {
      setSearchError(err as Error);
      message.error(t('error.unknown'));
    } finally {
      setIsSearching(false);
    }
  }, [addToHistory, t]);
  
  const handleHistorySelect = useCallback((query: string) => {
    handleSearch(query, 3);
  }, [handleSearch]);
  
  const handleRetrySearch = useCallback(() => {
    if (searchParams) {
      handleSearch(searchParams.query, searchParams.top_k);
    }
  }, [searchParams, handleSearch]);
  
  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 16px' }}>
      {/* Hero Section */}
      <Space direction="vertical" size="small" style={{ marginBottom: 32 }}>
        <Tag color="orange">Offline Retrieval-Augmented Generation</Tag>
        <Title level={1} style={{ margin: 0 }}>{t('app.subtitle')}</Title>
        <Paragraph type="secondary" style={{ maxWidth: 720 }}>
          {t('app.description')}
        </Paragraph>
      </Space>
      
      {/* Main Content */}
      <Row gutter={[24, 24]}>
        {/* Left Column - Search & Library */}
        <Col xs={24} lg={10}>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <SearchForm onSearch={handleSearch} loading={isSearching} />
            <SearchHistory onSelect={handleHistorySelect} />
            <LibraryPanel
              data={libraryData}
              loading={isLibraryLoading}
              error={libraryError}
              onReload={() => reloadLibrary()}
            />
          </Space>
        </Col>
        
        {/* Right Column - Results */}
        <Col xs={24} lg={14}>
          <ResultPanel
            data={searchResult}
            loading={isSearching}
            error={searchError}
            query={searchParams?.query}
            onRetry={handleRetrySearch}
          />
        </Col>
      </Row>
    </div>
  );
};
```

- [ ] **步骤 2: 创建 App.tsx**

```typescript
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { MainLayout } from '@/layouts/MainLayout/MainLayout';
import { Home } from '@/pages/Home/Home';
import { ErrorBoundary } from '@/components/ErrorBoundary/ErrorBoundary';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <MainLayout>
          <Home />
        </MainLayout>
      </ErrorBoundary>
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  );
};
```

- [ ] **步骤 3: 创建 main.tsx**

```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';
import '@/i18n';
import '@/styles/global.less';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

---

### Phase 13: 环境配置

#### Task 13: 创建环境配置文件

**文件:**
- 创建: `web-new/.env`
- 创建: `web-new/.env.production`
- 创建: `web-new/.env.example`

**步骤:**

- [ ] **步骤 1: 创建 .env**

```
VITE_APP_TITLE=Tiny RAG Demo
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_VERSION=1.0.0
```

- [ ] **步骤 2: 创建 .env.production**

```
VITE_APP_TITLE=Tiny RAG Demo
VITE_API_BASE_URL=/api
VITE_APP_VERSION=1.0.0
```

---

### Phase 14: 构建和部署说明

#### Task 14: 创建构建脚本和文档

**文件:**
- 创建: `web-new/README.md`

**步骤:**

- [ ] **步骤 1: 创建 README.md**

```markdown
# Tiny RAG Demo - 生产级前端

基于 React 18 + TypeScript + Vite + Ant Design 构建的现代化 RAG 演示界面。

## 特性

- React 18 + TypeScript 5.x
- Vite 5.x 构建工具
- Ant Design 5.x UI 组件库
- React Query 数据管理
- Zustand 状态管理
- i18next 国际化支持
- 暗黑模式支持
- 代码分割和懒加载
- Markdown 渲染和代码高亮
- 搜索历史和结果高亮

## 快速开始

### 安装依赖

```bash
npm install
```

### 开发环境

```bash
npm run dev
```

### 构建生产版本

```bash
npm run build
```

### 预览生产版本

```bash
npm run preview
```

### 代码检查

```bash
npm run lint
npm run typecheck
```

### 测试

```bash
npm run test
```

## 项目结构

```
src/
├── components/     # 公共组件
├── features/       # 功能模块
├── hooks/          # 全局 Hooks
├── i18n/           # 国际化
├── layouts/        # 布局组件
├── pages/          # 页面组件
├── services/       # API 服务
├── stores/         # 全局状态
├── styles/         # 全局样式
├── types/          # 类型定义
└── utils/          # 工具函数
```

## 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| VITE_API_BASE_URL | API 基础地址 | http://localhost:8000 |
| VITE_APP_TITLE | 应用标题 | Tiny RAG Demo |

## 部署

### Docker 部署

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### 静态托管

构建完成后，将 `dist` 目录部署到任意静态托管服务：
- Vercel
- Netlify
- GitHub Pages
- AWS S3 + CloudFront
- 腾讯云 COS
- 阿里云 OSS

## License

MIT
```

---

## 验证清单

- [ ] TypeScript 编译通过 (`npm run typecheck`)
- [ ] ESLint 检查通过 (`npm run lint`)
- [ ] 构建成功 (`npm run build`)
- [ ] 所有功能正常工作
- [ ] 暗黑模式切换正常
- [ ] 国际化切换正常
- [ ] 响应式布局正常
- [ ] 搜索历史保存正常
- [ ] Markdown 渲染正常
- [ ] 代码高亮正常
- [ ] 错误边界捕获正常

---

## 提交信息

```
feat: 前端重构 - 迁移到 React + TypeScript + Vite

- 使用 React 18 + TypeScript 5.x 重构
- 添加 Vite 5.x 构建工具
- 集成 Ant Design 5.x UI 组件库
- 添加 React Query 数据管理
- 添加 Zustand 状态管理
- 实现 i18next 国际化支持
- 添加暗黑模式支持
- 实现代码分割和懒加载
- 添加 Markdown 渲染和代码高亮
- 添加搜索历史和结果高亮
- 完善错误处理和重试机制
- 添加响应式布局优化
```

# Tiny RAG Demo - 生产级前端

基于 React 18 + TypeScript + Vite + Ant Design 构建的现代化 RAG 演示界面。

## 特性

- **React 18 + TypeScript 5.x** - 现代化开发体验
- **Vite 5.x** - 极速构建工具
- **Ant Design 5.x** - 企业级 UI 组件库
- **React Query (TanStack Query)** - 服务端状态管理
- **Zustand** - 客户端状态管理
- **i18next** - 国际化支持（中英文）
- **暗黑模式** - 自动跟随系统或手动切换
- **代码分割** - 自动代码分割和懒加载
- **Markdown 渲染** - 支持代码高亮
- **搜索历史** - 本地存储搜索记录
- **响应式设计** - 完美适配移动端和桌面端

## 快速开始

### 安装依赖

```bash
cd web-new
npm install
```

### 开发环境

```bash
npm run dev
```

应用将在 http://localhost:3000 启动

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
# TypeScript 类型检查
npm run typecheck

# ESLint 代码检查
npm run lint

# 自动修复 ESLint 问题
npm run lint:fix
```

### 测试

```bash
npm run test
npm run coverage
```

### 分析构建包大小

```bash
npm run build:analyze
```

## 项目结构

```
web-new/
├── package.json              # 依赖管理
├── tsconfig.json             # TypeScript 配置
├── vite.config.ts            # Vite 构建配置
├── index.html                # 入口 HTML
├── .env                      # 环境变量
├── src/
│   ├── main.tsx              # 应用入口
│   ├── App.tsx               # 根组件
│   ├── vite-env.d.ts         # Vite 类型声明
│   ├── components/           # 公共组件
│   │   ├── ErrorBoundary/    # 错误边界
│   │   └── ThemeToggle/      # 主题切换
│   ├── features/             # 功能模块
│   │   ├── search/           # 搜索模块
│   │   ├── library/          # 文档库模块
│   │   └── result/           # 结果展示模块
│   ├── hooks/                # 全局 Hooks
│   ├── i18n/                 # 国际化配置
│   ├── layouts/              # 布局组件
│   ├── pages/                # 页面组件
│   ├── services/             # API 服务
│   ├── stores/               # 全局状态
│   ├── styles/               # 全局样式
│   ├── types/                # 类型定义
│   └── utils/                # 工具函数
└── public/                   # 静态资源
```

## 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| VITE_API_BASE_URL | API 基础地址 | http://localhost:8000 |
| VITE_APP_TITLE | 应用标题 | Tiny RAG Demo |
| VITE_APP_VERSION | 应用版本 | 1.0.0 |

## 技术栈详情

### 核心依赖
- **React 18.2** - UI 框架
- **React DOM 18.2** - DOM 渲染
- **TypeScript 5.3** - 类型系统
- **Vite 5.0** - 构建工具

### UI 组件
- **Ant Design 5.12** - 组件库
- **@ant-design/icons** - 图标库

### 状态管理
- **Zustand 4.4** - 全局状态管理
- **@tanstack/react-query 5.13** - 服务端状态管理

### 国际化
- **i18next 23.7** - 国际化核心
- **react-i18next 13.5** - React 集成
- **i18next-browser-languagedetector 7.2** - 语言检测

### 工具
- **Axios 1.6** - HTTP 客户端
- **PrismJS 1.29** - 代码高亮
- **DayJS 1.11** - 日期处理
- **Lodash ES 4.17** - 工具函数

### 开发工具
- **ESLint 8.55** - 代码检查
- **Prettier 3.1** - 代码格式化
- **Vitest 1.1** - 测试框架

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

- **Vercel** - `vercel --prod`
- **Netlify** - 拖拽上传或 Git 集成
- **GitHub Pages** - Actions 自动部署
- **AWS S3 + CloudFront** - CDN 加速
- **腾讯云 COS** - 国内 CDN
- **阿里云 OSS** - 国内 CDN

### 生产环境配置

1. 修改 `.env.production` 中的 `VITE_API_BASE_URL` 为生产环境 API 地址
2. 运行 `npm run build` 生成生产包
3. 将 `dist` 目录部署到服务器

## 开发指南

### 添加新页面

1. 在 `src/pages/` 下创建新页面组件
2. 在 `App.tsx` 中添加路由
3. 添加对应的国际化词条

### 添加新功能模块

1. 在 `src/features/` 下创建功能目录
2. 创建 `components/`, `hooks/`, `stores/` 子目录
3. 遵循功能优先的目录结构

### 添加新的 API 接口

1. 在 `src/services/api.ts` 中添加 API 方法
2. 在 `src/types/index.ts` 中添加类型定义
3. 在 `src/hooks/` 中创建对应的 React Query Hook

### 添加国际化

1. 在 `src/i18n/locales/zh-CN.json` 和 `en-US.json` 中添加词条
2. 在组件中使用 `const { t } = useTranslation()`
3. 使用 `t('key.subkey')` 获取翻译

## 浏览器支持

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License

MIT License

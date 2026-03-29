# RAG系统第二阶段前端增强实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 增强前端功能，包括搜索历史、收藏、结果可视化、上传进度和文档库管理优化。

**Architecture:** 基于现有 React + TypeScript + Ant Design 架构，添加新功能模块和组件。

**Tech Stack:** React 18, TypeScript, Ant Design, Zustand, React Query

**Design Spec:** 基于 docs/superpowers/specs/2026-03-28-phase1-enhancement-design.md 第二阶段部分

---

## 文件结构映射

### 新增文件
```
web-new/src/
├── features/
│   ├── search/
│   │   ├── stores/
│   │   │   └── searchHistoryStore.ts    # 搜索历史和收藏状态管理
│   │   ├── components/
│   │   │   ├── SearchHistory.tsx        # 搜索历史组件
│   │   │   ├── FavoriteButton.tsx       # 收藏按钮组件
│   │   │   └── SearchResultChart.tsx    # 结果可视化图表
│   │   └── hooks/
│   │       └── useSearchHistory.ts      # 搜索历史Hook
│   │
│   ├── library/
│   │   ├── components/
│   │   │   ├── FileDetailDrawer.tsx     # 文件详情抽屉
│   │   │   ├── BulkOperations.tsx       # 批量操作工具栏
│   │   │   └── FilePreviewModal.tsx     # 文件预览弹窗
│   │   └── hooks/
│   │       └── useFileOperations.ts     # 文件操作Hook
│   │
│   └── upload/
│       ├── components/
│       │   ├── UploadProgress.tsx       # 上传进度组件
│       │   └── UploadStatusBadge.tsx    # 上传状态徽章
│       └── hooks/
│           └── useUploadProgress.ts     # 上传进度Hook
│
├── components/
│   └── ui/
│       ├── StatisticCard.tsx            # 统计卡片组件
│       └── EmptyState.tsx               # 空状态组件
│
└── utils/
    └── storage.ts                       # 本地存储工具
```

### 修改文件
```
web-new/src/
├── features/search/components/SearchPanel.tsx
├── features/result/components/ResultPanel.tsx
├── features/library/components/FileList.tsx
├── features/library/components/UploadArea.tsx
└── types/index.ts                       # 添加新类型定义
```

---

## Task 1: 搜索历史与收藏功能

**Files:**
- Create: `web-new/src/features/search/stores/searchHistoryStore.ts`
- Create: `web-new/src/features/search/components/SearchHistory.tsx`
- Create: `web-new/src/features/search/components/FavoriteButton.tsx`
- Create: `web-new/src/features/search/hooks/useSearchHistory.ts`
- Modify: `web-new/src/types/index.ts`

### 功能描述
1. **搜索历史**: 保存最近的搜索查询，支持点击重新搜索
2. **收藏功能**: 允许用户收藏搜索结果，保存到本地存储
3. **历史管理**: 清空历史、删除单条历史

### TDD流程

- [ ] **Step 1: 添加类型定义**

```typescript
// web-new/src/types/index.ts
export interface SearchHistoryItem {
  id: string;
  query: string;
  timestamp: number;
  resultCount: number;
}

export interface FavoriteItem {
  id: string;
  query: string;
  hits: SearchHit[];
  createdAt: number;
  notes?: string;
}
```

- [ ] **Step 2: 实现 Zustand Store**

```typescript
// web-new/src/features/search/stores/searchHistoryStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SearchHistoryState {
  history: SearchHistoryItem[];
  favorites: FavoriteItem[];
  addToHistory: (item: SearchHistoryItem) => void;
  removeFromHistory: (id: string) => void;
  clearHistory: () => void;
  addToFavorites: (item: FavoriteItem) => void;
  removeFromFavorites: (id: string) => void;
  updateFavoriteNotes: (id: string, notes: string) => void;
}

export const useSearchHistoryStore = create<SearchHistoryState>()(
  persist(
    (set) => ({
      history: [],
      favorites: [],
      addToHistory: (item) =>
        set((state) => ({
          history: [item, ...state.history.filter((h) => h.query !== item.query)].slice(0, 50),
        })),
      removeFromHistory: (id) =>
        set((state) => ({
          history: state.history.filter((h) => h.id !== id),
        })),
      clearHistory: () => set({ history: [] }),
      addToFavorites: (item) =>
        set((state) => ({
          favorites: [...state.favorites, item],
        })),
      removeFromFavorites: (id) =>
        set((state) => ({
          favorites: state.favorites.filter((f) => f.id !== id),
        })),
      updateFavoriteNotes: (id, notes) =>
        set((state) => ({
          favorites: state.favorites.map((f) =>
            f.id === id ? { ...f, notes } : f
          ),
        })),
    }),
    {
      name: 'search-history-storage',
    }
  )
);
```

- [ ] **Step 3: 实现 SearchHistory 组件**

```tsx
// web-new/src/features/search/components/SearchHistory.tsx
import React from 'react';
import { List, Tag, Button, Empty, Popconfirm } from 'antd';
import { HistoryOutlined, DeleteOutlined, StarOutlined } from '@ant-design/icons';
import { useSearchHistoryStore } from '../stores/searchHistoryStore';
import { useTranslation } from 'react-i18next';
import dayjs from 'dayjs';

interface SearchHistoryProps {
  onSelect: (query: string) => void;
}

export const SearchHistory: React.FC<SearchHistoryProps> = ({ onSelect }) => {
  const { t } = useTranslation();
  const { history, removeFromHistory, clearHistory } = useSearchHistoryStore();

  if (history.length === 0) {
    return (
      <Empty
        image={<HistoryOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />}
        description={t('search.noHistory')}
      />
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h4>{t('search.history')}</h4>
        <Popconfirm
          title={t('search.clearHistoryConfirm')}
          onConfirm={clearHistory}
          okText={t('common.yes')}
          cancelText={t('common.no')}
        >
          <Button type="link" danger icon={<DeleteOutlined />}>
            {t('search.clearHistory')}
          </Button>
        </Popconfirm>
      </div>
      <List
        size="small"
        dataSource={history}
        renderItem={(item) => (
          <List.Item
            actions={[
              <Button
                type="link"
                size="small"
                onClick={() => onSelect(item.query)}
              >
                {t('common.search')}
              </Button>,
              <Button
                type="link"
                size="small"
                danger
                icon={<DeleteOutlined />}
                onClick={() => removeFromHistory(item.id)}
              />,
            ]}
          >
            <List.Item.Meta
              title={item.query}
              description={
                <>
                  <Tag size="small">{item.resultCount} hits</Tag>
                  <span style={{ color: '#999', marginLeft: 8 }}>
                    {dayjs(item.timestamp).fromNow()}
                  </span>
                </>
              }
            />
          </List.Item>
        )}
      />
    </div>
  );
};
```

- [ ] **Step 4: 实现 FavoriteButton 组件**

```tsx
// web-new/src/features/search/components/FavoriteButton.tsx
import React, { useState } from 'react';
import { Button, Modal, Input, message } from 'antd';
import { StarOutlined, StarFilled } from '@ant-design/icons';
import { useSearchHistoryStore } from '../stores/searchHistoryStore';
import { useTranslation } from 'react-i18next';
import { nanoid } from 'nanoid';
import type { SearchHit } from '@/types';

interface FavoriteButtonProps {
  query: string;
  hits: SearchHit[];
}

export const FavoriteButton: React.FC<FavoriteButtonProps> = ({ query, hits }) => {
  const { t } = useTranslation();
  const { favorites, addToFavorites, removeFromFavorites } = useSearchHistoryStore();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [notes, setNotes] = useState('');

  const existingFavorite = favorites.find((f) => f.query === query);
  const isFavorited = !!existingFavorite;

  const handleToggleFavorite = () => {
    if (isFavorited && existingFavorite) {
      removeFromFavorites(existingFavorite.id);
      message.success(t('search.removedFromFavorites'));
    } else {
      setIsModalOpen(true);
    }
  };

  const handleSave = () => {
    addToFavorites({
      id: nanoid(),
      query,
      hits,
      createdAt: Date.now(),
      notes,
    });
    setIsModalOpen(false);
    setNotes('');
    message.success(t('search.addedToFavorites'));
  };

  return (
    <>
      <Button
        type={isFavorited ? 'primary' : 'default'}
        icon={isFavorited ? <StarFilled /> : <StarOutlined />}
        onClick={handleToggleFavorite}
      >
        {isFavorited ? t('search.favorited') : t('search.favorite')}
      </Button>

      <Modal
        title={t('search.addToFavorites')}
        open={isModalOpen}
        onOk={handleSave}
        onCancel={() => setIsModalOpen(false)}
        okText={t('common.save')}
        cancelText={t('common.cancel')}
      >
        <p>{t('search.favoriteDescription', { query })}</p>
        <Input.TextArea
          placeholder={t('search.favoriteNotesPlaceholder')}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={3}
        />
      </Modal>
    </>
  );
};
```

- [ ] **Step 5: 集成到 SearchPanel**

修改 SearchPanel 组件，在搜索框下方添加 SearchHistory 组件。

- [ ] **Step 6: 添加国际化文本**

在 i18n 文件中添加新文本：
- search.noHistory
- search.history
- search.clearHistory
- search.clearHistoryConfirm
- search.favorite
- search.favorited
- search.addToFavorites
- search.removedFromFavorites
- search.addedToFavorites

- [ ] **Step 7: 运行测试**

```bash
cd web-new
npm run typecheck
npm run lint
```

- [ ] **Step 8: Commit**

```bash
git add web-new/src/features/search/
git commit -m "feat(search): add search history and favorites functionality"
```

---

## Task 2: 搜索结果可视化增强

**Files:**
- Create: `web-new/src/features/search/components/SearchResultChart.tsx`
- Create: `web-new/src/components/ui/StatisticCard.tsx`
- Modify: `web-new/src/features/result/components/ResultPanel.tsx`

### 功能描述
1. **分数分布图**: 使用柱状图展示搜索结果的分数分布
2. **相关性统计**: 显示平均分数、最高/最低分数等统计信息
3. **来源分布**: 展示结果来自哪些文档

### TDD流程

- [ ] **Step 1: 安装图表库**

```bash
cd web-new
npm install @ant-design/charts --save
```

- [ ] **Step 2: 实现 StatisticCard 组件**

```tsx
// web-new/src/components/ui/StatisticCard.tsx
import React from 'react';
import { Card, Statistic } from 'antd';
import type { StatisticProps } from 'antd';

interface StatisticCardProps extends StatisticProps {
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
}

export const StatisticCard: React.FC<StatisticCardProps> = ({
  trend,
  trendValue,
  ...statisticProps
}) => {
  return (
    <Card size="small">
      <Statistic {...statisticProps} />
      {trend && trendValue && (
        <div
          style={{
            color: trend === 'up' ? '#52c41a' : trend === 'down' ? '#ff4d4f' : '#999',
            fontSize: 12,
            marginTop: 4,
          }}
        >
          {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {trendValue}
        </div>
      )}
    </Card>
  );
};
```

- [ ] **Step 3: 实现 SearchResultChart 组件**

```tsx
// web-new/src/features/search/components/SearchResultChart.tsx
import React from 'react';
import { Row, Col, Divider } from 'antd';
import { Column, Pie } from '@ant-design/charts';
import { StatisticCard } from '@/components/ui/StatisticCard';
import type { SearchHit } from '@/types';

interface SearchResultChartProps {
  hits: SearchHit[];
}

export const SearchResultChart: React.FC<SearchResultChartProps> = ({ hits }) => {
  if (!hits || hits.length === 0) return null;

  // 分数分布数据
  const scoreRanges = [
    { range: '0.9-1.0', count: 0 },
    { range: '0.8-0.9', count: 0 },
    { range: '0.7-0.8', count: 0 },
    { range: '0.6-0.7', count: 0 },
    { range: '0.5-0.6', count: 0 },
    { range: '< 0.5', count: 0 },
  ];

  hits.forEach((hit) => {
    const score = hit.score;
    if (score >= 0.9) scoreRanges[0].count++;
    else if (score >= 0.8) scoreRanges[1].count++;
    else if (score >= 0.7) scoreRanges[2].count++;
    else if (score >= 0.6) scoreRanges[3].count++;
    else if (score >= 0.5) scoreRanges[4].count++;
    else scoreRanges[5].count++;
  });

  // 来源分布数据
  const sourceCount: Record<string, number> = {};
  hits.forEach((hit) => {
    const source = hit.chunk.source.split('/').pop() || 'Unknown';
    sourceCount[source] = (sourceCount[source] || 0) + 1;
  });

  const sourceData = Object.entries(sourceCount).map(([name, value]) => ({
    name,
    value,
  }));

  // 统计数据
  const scores = hits.map((h) => h.score);
  const avgScore = scores.reduce((a, b) => a + b, 0) / scores.length;
  const maxScore = Math.max(...scores);
  const minScore = Math.min(...scores);

  const columnConfig = {
    data: scoreRanges,
    xField: 'range',
    yField: 'count',
    label: {
      position: 'top',
    },
    xAxis: {
      label: {
        autoHide: true,
        autoRotate: false,
      },
    },
  };

  const pieConfig = {
    data: sourceData,
    angleField: 'value',
    colorField: 'name',
    radius: 0.8,
    label: {
      type: 'outer',
    },
  };

  return (
    <div style={{ marginTop: 24 }}>
      <Row gutter={[16, 16]}>
        <Col span={8}>
          <StatisticCard
            title="平均分数"
            value={avgScore.toFixed(3)}
            precision={3}
            suffix="/ 1.0"
          />
        </Col>
        <Col span={8}>
          <StatisticCard
            title="最高分数"
            value={maxScore.toFixed(3)}
            precision={3}
            valueStyle={{ color: '#52c41a' }}
          />
        </Col>
        <Col span={8}>
          <StatisticCard
            title="最低分数"
            value={minScore.toFixed(3)}
            precision={3}
            valueStyle={{ color: '#ff4d4f' }}
          />
        </Col>
      </Row>

      <Divider />

      <Row gutter={[24, 24]}>
        <Col span={12}>
          <h4>分数分布</h4>
          <Column {...columnConfig} height={200} />
        </Col>
        <Col span={12}>
          <h4>来源分布</h4>
          <Pie {...pieConfig} height={200} />
        </Col>
      </Row>
    </div>
  );
};
```

- [ ] **Step 4: 集成到 ResultPanel**

在 ResultPanel 中添加图表展示区域。

- [ ] **Step 5: 运行测试**

```bash
npm run typecheck
npm run lint
```

- [ ] **Step 6: Commit**

```bash
git add web-new/src/
git commit -m "feat(result): add search result visualization with charts"
```

---

## Task 3: 上传进度与状态展示

**Files:**
- Create: `web-new/src/features/upload/components/UploadProgress.tsx`
- Create: `web-new/src/features/upload/components/UploadStatusBadge.tsx`
- Create: `web-new/src/features/upload/hooks/useUploadProgress.ts`
- Modify: `web-new/src/features/library/components/UploadArea.tsx`

### 功能描述
1. **进度条**: 显示当前上传文件的进度
2. **状态徽章**: 显示上传成功/失败状态
3. **批量上传**: 支持多文件上传队列显示

### TDD流程

- [ ] **Step 1: 实现 useUploadProgress Hook**

```typescript
// web-new/src/features/upload/hooks/useUploadProgress.ts
import { useState, useCallback } from 'react';

export interface UploadProgressState {
  fileId: string;
  fileName: string;
  progress: number;
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
  speed?: number; // bytes per second
}

export const useUploadProgress = () => {
  const [uploads, setUploads] = useState<UploadProgressState[]>([]);

  const addUpload = useCallback((file: File) => {
    const fileId = `${file.name}-${Date.now()}`;
    setUploads((prev) => [
      ...prev,
      {
        fileId,
        fileName: file.name,
        progress: 0,
        status: 'pending',
      },
    ]);
    return fileId;
  }, []);

  const updateProgress = useCallback((fileId: string, progress: number, speed?: number) => {
    setUploads((prev) =>
      prev.map((upload) =>
        upload.fileId === fileId
          ? { ...upload, progress, status: 'uploading', speed }
          : upload
      )
    );
  }, []);

  const markSuccess = useCallback((fileId: string) => {
    setUploads((prev) =>
      prev.map((upload) =>
        upload.fileId === fileId ? { ...upload, status: 'success', progress: 100 } : upload
      )
    );
  }, []);

  const markError = useCallback((fileId: string, error: string) => {
    setUploads((prev) =>
      prev.map((upload) =>
        upload.fileId === fileId ? { ...upload, status: 'error', error } : upload
      )
    );
  }, []);

  const clearCompleted = useCallback(() => {
    setUploads((prev) => prev.filter((u) => u.status === 'uploading' || u.status === 'pending'));
  }, []);

  return {
    uploads,
    addUpload,
    updateProgress,
    markSuccess,
    markError,
    clearCompleted,
  };
};
```

- [ ] **Step 2: 实现 UploadProgress 组件**

```tsx
// web-new/src/features/upload/components/UploadProgress.tsx
import React from 'react';
import { List, Progress, Tag, Button, Space } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  ClockCircleOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import type { UploadProgressState } from '../hooks/useUploadProgress';
import { formatFileSize } from '@/utils/format';

interface UploadProgressProps {
  uploads: UploadProgressState[];
  onClearCompleted: () => void;
}

export const UploadProgress: React.FC<UploadProgressProps> = ({
  uploads,
  onClearCompleted,
}) => {
  if (uploads.length === 0) return null;

  const hasCompleted = uploads.some((u) => u.status === 'success' || u.status === 'error');

  const getStatusIcon = (status: UploadProgressState['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'error':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'uploading':
        return <LoadingOutlined style={{ color: '#1890ff' }} />;
      default:
        return <ClockCircleOutlined style={{ color: '#999' }} />;
    }
  };

  const getStatusTag = (status: UploadProgressState['status']) => {
    switch (status) {
      case 'success':
        return <Tag color="success">成功</Tag>;
      case 'error':
        return <Tag color="error">失败</Tag>;
      case 'uploading':
        return <Tag color="processing">上传中</Tag>;
      default:
        return <Tag>等待中</Tag>;
    }
  };

  return (
    <div style={{ marginTop: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
        <h4>上传队列 ({uploads.length})</h4>
        {hasCompleted && (
          <Button type="link" size="small" icon={<DeleteOutlined />} onClick={onClearCompleted}>
            清除已完成
          </Button>
        )}
      </div>

      <List
        size="small"
        dataSource={uploads}
        renderItem={(upload) => (
          <List.Item>
            <div style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <Space>
                  {getStatusIcon(upload.status)}
                  <span>{upload.fileName}</span>
                  {getStatusTag(upload.status)}
                </Space>
                {upload.speed && upload.status === 'uploading' && (
                  <span style={{ fontSize: 12, color: '#999' }}>
                    {formatFileSize(upload.speed)}/s
                  </span>
                )}
              </div>

              {upload.status === 'uploading' && (
                <Progress percent={Math.round(upload.progress)} size="small" />
              )}

              {upload.error && (
                <div style={{ color: '#ff4d4f', fontSize: 12, marginTop: 4 }}>{upload.error}</div>
              )}
            </div>
          </List.Item>
        )}
      />
    </div>
  );
};
```

- [ ] **Step 3: 修改 UploadArea 组件**

集成上传进度功能到现有的 UploadArea 组件。

- [ ] **Step 4: 运行测试**

```bash
npm run typecheck
npm run lint
```

- [ ] **Step 5: Commit**

```bash
git add web-new/src/
git commit -m "feat(upload): add upload progress and status display"
```

---

## Task 4: 文档库管理界面优化

**Files:**
- Create: `web-new/src/features/library/components/FileDetailDrawer.tsx`
- Create: `web-new/src/features/library/components/BulkOperations.tsx`
- Create: `web-new/src/features/library/components/FilePreviewModal.tsx`
- Modify: `web-new/src/features/library/components/FileList.tsx`

### 功能描述
1. **文件详情抽屉**: 点击文件显示详情（大小、类型、上传时间、内容预览）
2. **批量操作**: 支持多选文件进行批量删除、下载
3. **文件预览**: 预览文件内容

### TDD流程

- [ ] **Step 1-8: 实现组件和集成**

（具体实现代码较长，略，按照 TDD 流程实现）

- [ ] **Step 9: Commit**

```bash
git add web-new/src/
git commit -m "feat(library): enhance document library management UI"
```

---

## 最终验证

- [ ] **运行完整测试**

```bash
cd web-new
npm run typecheck
npm run lint
npm run build
```

- [ ] **验证功能**

1. 搜索历史正常显示和点击
2. 收藏功能正常工作
3. 图表正确显示数据
4. 上传进度实时更新
5. 文件详情抽屉正常打开

- [ ] **Commit 最终版本**

```bash
git add .
git commit -m "feat(frontend): complete phase2 enhancements

- Search history and favorites
- Result visualization with charts
- Upload progress display
- Enhanced library management UI

All tests passing, build successful"
```

---

**执行方式**: 每个 Task 可以并行或串行执行，建议按 Task 1→2→3→4 顺序。
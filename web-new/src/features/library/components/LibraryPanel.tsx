import React from 'react';
import { Card, List, Typography, Tag, Space, Button, Skeleton, Alert, Divider } from 'antd';
import { ReloadOutlined, FileTextOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import type { LibraryInfo } from '@/types';
import { UploadArea } from './UploadArea';
import { FileList } from './FileList';
import { UploadHistory } from './UploadHistory';

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
      style={{ marginTop: 24 }}
    >
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Paragraph>
          已入库 {data.documents} 个文档，切分为 {data.chunks} 个 chunk
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
        
        <Divider />
        
        <UploadArea onUploadSuccess={onReload} />
        
        <Divider />
        
        <FileList files={data.files} onDelete={onReload} />
        
        <Divider />
        
        <UploadHistory />
      </Space>
    </Card>
  );
};

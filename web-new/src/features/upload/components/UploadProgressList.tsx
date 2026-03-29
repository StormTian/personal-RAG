import React from 'react';
import { List, Progress, Button, Space, Typography, Tag, Tooltip } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  ClockCircleOutlined,
  DeleteOutlined,
  FileOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import type { UploadFile } from '../hooks/useUploadProgress';

interface UploadProgressListProps {
  uploads: UploadFile[];
  onClearCompleted: () => void;
  onClearAll: () => void;
}

const { Text } = Typography;

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

const formatSpeed = (bytesPerSecond?: number): string => {
  if (!bytesPerSecond || bytesPerSecond === 0) return '';
  return `${formatFileSize(bytesPerSecond)}/s`;
};

export const UploadProgressList: React.FC<UploadProgressListProps> = ({
  uploads,
  onClearCompleted,
  onClearAll,
}) => {
  const { t } = useTranslation();

  if (uploads.length === 0) return null;

  const getStatusIcon = (status: UploadFile['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 16 }} />;
      case 'error':
        return <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 16 }} />;
      case 'uploading':
        return <LoadingOutlined style={{ color: '#1890ff', fontSize: 16 }} />;
      default:
        return <ClockCircleOutlined style={{ color: '#999', fontSize: 16 }} />;
    }
  };

  const getStatusTag = (status: UploadFile['status']) => {
    switch (status) {
      case 'success':
        return <Tag color="success">{t('upload.statusSuccess')}</Tag>;
      case 'error':
        return <Tag color="error">{t('upload.statusError')}</Tag>;
      case 'uploading':
        return <Tag color="processing">{t('upload.statusUploading')}</Tag>;
      default:
        return <Tag>{t('upload.statusPending')}</Tag>;
    }
  };

  const hasCompleted = uploads.some((u) => u.status === 'success' || u.status === 'error');

  return (
    <div style={{ marginTop: 16, padding: 16, backgroundColor: '#f6ffed', borderRadius: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <Text strong>
          {t('upload.queueTitle')} ({uploads.length})
        </Text>
        <Space>
          {hasCompleted && (
            <Button type="link" size="small" onClick={onClearCompleted}>
              {t('upload.clearCompleted')}
            </Button>
          )}
          <Button type="link" size="small" danger onClick={onClearAll} icon={<DeleteOutlined />}>
            {t('upload.clearAll')}
          </Button>
        </Space>
      </div>

      <List
        size="small"
        dataSource={uploads}
        renderItem={(upload) => (
          <List.Item style={{ padding: '8px 0' }}>
            <div style={{ width: '100%' }}>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
                <Space style={{ flex: 1 }}>
                  {getStatusIcon(upload.status)}
                  <FileOutlined />
                  <Tooltip title={upload.name}>
                    <Text style={{ maxWidth: 200 }} ellipsis>
                      {upload.name}
                    </Text>
                  </Tooltip>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    ({formatFileSize(upload.size)})
                  </Text>
                  {getStatusTag(upload.status)}
                </Space>
                {upload.speed && upload.status === 'uploading' && (
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {formatSpeed(upload.speed)}
                  </Text>
                )}
              </div>

              {upload.status === 'uploading' && (
                <Progress
                  percent={Math.round(upload.progress)}
                  size="small"
                  strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }}
                />
              )}

              {upload.error && (
                <Text type="danger" style={{ fontSize: 12 }}>
                  {upload.error}
                </Text>
              )}
            </div>
          </List.Item>
        )}
      />
    </div>
  );
};

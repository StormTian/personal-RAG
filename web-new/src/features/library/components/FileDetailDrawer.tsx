import React from 'react';
import { Drawer, Descriptions, Tag, Space, Typography, Button } from 'antd';
import { FileOutlined, DownloadOutlined, DeleteOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import type { FileItem } from './FileList';

const { Title, Text } = Typography;

interface FileDetailDrawerProps {
  file: FileItem | null;
  visible: boolean;
  onClose: () => void;
  onDelete: (filename: string) => void;
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const FileDetailDrawer: React.FC<FileDetailDrawerProps> = ({
  file,
  visible,
  onClose,
  onDelete,
}) => {
  const { t } = useTranslation();

  if (!file) return null;

  const filename = file.name || file.source || 'unknown';
  const fileType = file.type || file.file_type || 'unknown';
  const fileSize = file.size || file.chars || 0;

  return (
    <Drawer
      title={
        <Space>
          <FileOutlined />
          {t('files.detailTitle')}
        </Space>
      }
      placement="right"
      onClose={onClose}
      open={visible}
      width={480}
      extra={
        <Space>
          <Button icon={<DownloadOutlined />} disabled>
            {t('common.download')}
          </Button>
          <Button
            danger
            icon={<DeleteOutlined />}
            onClick={() => {
              onDelete(filename);
              onClose();
            }}
          >
            {t('common.delete')}
          </Button>
        </Space>
      }
    >
      <Descriptions bordered column={1} size="small">
        <Descriptions.Item label={t('files.filename')}>
          <Text strong>{filename}</Text>
        </Descriptions.Item>
        <Descriptions.Item label={t('files.fileType')}>
          <Tag color="blue">{fileType.toUpperCase()}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label={t('files.fileSize')}>
          {formatFileSize(fileSize)}
        </Descriptions.Item>
        <Descriptions.Item label={t('files.title')}>
          {file.title || '-'}
        </Descriptions.Item>
        <Descriptions.Item label={t('files.chars')}>
          {file.chars?.toLocaleString() || '-'}
        </Descriptions.Item>
        <Descriptions.Item label={t('files.modifiedAt')}>
          {file.modified_at
            ? new Date(file.modified_at).toLocaleString()
            : '-'}
        </Descriptions.Item>
        <Descriptions.Item label={t('files.sourcePath')}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {file.source || '-'}
          </Text>
        </Descriptions.Item>
      </Descriptions>

      <div style={{ marginTop: 24 }}>
        <Title level={5}>{t('files.previewTitle')}</Title>
        <Text type="secondary">
          {t('files.previewNotAvailable')}
        </Text>
      </div>
    </Drawer>
  );
};

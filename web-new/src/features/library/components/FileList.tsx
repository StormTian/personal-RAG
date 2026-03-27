import React, { useState } from 'react';
import { List, Button, Popconfirm, Tag, Space, Typography, message } from 'antd';
import { FileOutlined, DeleteOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { filesApi } from '@/services/api';

const { Text } = Typography;

export interface FileItem {
  name?: string;
  source?: string;
  size?: number;
  chars?: number;
  modified_at?: string;
  type?: string;
  file_type?: string;
  title?: string;
}

export interface FileListProps {
  files: FileItem[];
  onDelete: () => void;
}

export const FileList: React.FC<FileListProps> = ({ files, onDelete }) => {
  const { t } = useTranslation();
  const [deleting, setDeleting] = useState<string | null>(null);

  const handleDelete = async (filename: string) => {
    setDeleting(filename);
    try {
      await filesApi.deleteFile(filename);
      message.success(t('files.deleteSuccess', { filename }));
      onDelete();
    } catch (error) {
      message.error(t('files.deleteError', { filename }));
    } finally {
      setDeleting(null);
    }
  };

  const getFilename = (file: FileItem): string => {
    return file.name || file.source || 'unknown';
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <List
      header={<Text strong>{t('files.title')}</Text>}
      dataSource={files}
      renderItem={(file) => (
        <List.Item
          actions={[
            <Popconfirm
              key="delete"
              title={t('files.deleteConfirm', { filename: getFilename(file) })}
              onConfirm={() => handleDelete(getFilename(file))}
              okText={t('common.confirm')}
              cancelText={t('common.cancel')}
            >
              <Button
                danger
                icon={<DeleteOutlined />}
                loading={deleting === getFilename(file)}
              >
                {t('common.delete')}
              </Button>
            </Popconfirm>,
          ]}
        >
          <List.Item.Meta
            avatar={<FileOutlined />}
            title={file.name || file.source || 'Unknown'}
            description={
              <Space>
                <Tag>{(file.type || file.file_type || 'unknown').toUpperCase()}</Tag>
                <Text type="secondary">{formatFileSize(file.size || file.chars || 0)}</Text>
                <Text type="secondary">
                  {file.modified_at ? new Date(file.modified_at).toLocaleString() : '-'}
                </Text>
              </Space>
            }
          />
        </List.Item>
      )}
      locale={{ emptyText: t('files.empty') }}
    />
  );
};

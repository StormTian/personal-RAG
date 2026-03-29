import React, { useState } from 'react';
import {
  List,
  Button,
  Popconfirm,
  Tag,
  Space,
  Typography,
  message,
  Checkbox,
} from 'antd';
import {
  FileOutlined,
  DeleteOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { filesApi } from '@/services/api';
import { FileDetailDrawer } from './FileDetailDrawer';
import { BulkOperations } from './BulkOperations';

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
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [detailFile, setDetailFile] = useState<FileItem | null>(null);
  const [detailVisible, setDetailVisible] = useState(false);

  const handleDelete = async (filename: string) => {
    setDeleting(filename);
    try {
      await filesApi.deleteFile(filename);
      message.success(t('files.deleteSuccess', { filename }));
      onDelete();
      // Remove from selection if present
      setSelectedFiles((prev) => {
        const newSet = new Set(prev);
        newSet.delete(filename);
        return newSet;
      });
    } catch (error) {
      message.error(t('files.deleteError', { filename }));
    } finally {
      setDeleting(null);
    }
  };

  const handleBulkDelete = async () => {
    const filesToDelete = Array.from(selectedFiles);
    let successCount = 0;
    let errorCount = 0;

    for (const filename of filesToDelete) {
      try {
        await filesApi.deleteFile(filename);
        successCount++;
      } catch (error) {
        errorCount++;
      }
    }

    if (successCount > 0) {
      message.success(
        t('files.bulkDeleteSuccess', { success: successCount, total: filesToDelete.length })
      );
      onDelete();
      setSelectedFiles(new Set());
    }
    if (errorCount > 0) {
      message.error(t('files.bulkDeleteError', { count: errorCount }));
    }
  };

  const handleSelect = (filename: string, checked: boolean) => {
    setSelectedFiles((prev) => {
      const newSet = new Set(prev);
      if (checked) {
        newSet.add(filename);
      } else {
        newSet.delete(filename);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    const allFilenames = files.map((f) => getFilename(f));
    setSelectedFiles(new Set(allFilenames));
  };

  const handleDeselectAll = () => {
    setSelectedFiles(new Set());
  };

  const handleClearSelection = () => {
    setSelectedFiles(new Set());
  };

  const handleShowDetail = (file: FileItem) => {
    setDetailFile(file);
    setDetailVisible(true);
  };

  const handleCloseDetail = () => {
    setDetailVisible(false);
    setDetailFile(null);
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
    <div>
      <BulkOperations
        selectedCount={selectedFiles.size}
        totalCount={files.length}
        onSelectAll={handleSelectAll}
        onDeselectAll={handleDeselectAll}
        onDeleteSelected={handleBulkDelete}
        onClearSelection={handleClearSelection}
      />

      <List
        dataSource={files}
        renderItem={(file) => {
          const filename = getFilename(file);
          const isSelected = selectedFiles.has(filename);

          return (
            <List.Item
              style={{
                backgroundColor: isSelected ? '#e6f7ff' : 'transparent',
                borderRadius: 4,
                padding: '12px 16px',
              }}
              actions={[
                <Button
                  key="detail"
                  type="text"
                  icon={<InfoCircleOutlined />}
                  onClick={() => handleShowDetail(file)}
                >
                  {t('common.detail')}
                </Button>,
                <Popconfirm
                  key="delete"
                  title={t('files.deleteConfirm', { filename })}
                  onConfirm={() => handleDelete(filename)}
                  okText={t('common.confirm')}
                  cancelText={t('common.cancel')}
                >
                  <Button
                    danger
                    icon={<DeleteOutlined />}
                    loading={deleting === filename}
                  >
                    {t('common.delete')}
                  </Button>
                </Popconfirm>,
              ]}
            >
              <List.Item.Meta
                avatar={
                  <Checkbox
                    checked={isSelected}
                    onChange={(e) => handleSelect(filename, e.target.checked)}
                    style={{ marginRight: 8 }}
                  />
                }
                title={
                  <Text
                    style={{ cursor: 'pointer' }}
                    onClick={() => handleShowDetail(file)}
                  >
                    {filename}
                  </Text>
                }
                description={
                  <Space>
                    <FileOutlined />
                    <Tag>{(file.type || file.file_type || 'unknown').toUpperCase()}</Tag>
                    <Text type="secondary">{formatFileSize(file.size || file.chars || 0)}</Text>
                    <Text type="secondary">
                      {file.modified_at
                        ? new Date(file.modified_at).toLocaleString()
                        : '-'}
                    </Text>
                  </Space>
                }
              />
            </List.Item>
          );
        }}
        locale={{ emptyText: t('files.empty') }}
      />

      <FileDetailDrawer
        file={detailFile}
        visible={detailVisible}
        onClose={handleCloseDetail}
        onDelete={handleDelete}
      />
    </div>
  );
};

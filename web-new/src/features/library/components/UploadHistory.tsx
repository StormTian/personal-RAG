import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, Tooltip } from 'antd';
import { useTranslation } from 'react-i18next';
import { uploadApi } from '@/services/api';
import type { UploadHistoryRecord } from '@/types';
import { formatFileSize, formatDateTime } from '@/utils/format';

const statusConfig: Record<string, { color: string; text: string }> = {
  success: { color: 'success', text: '成功' },
  failed: { color: 'error', text: '失败' },
  pending: { color: 'warning', text: '处理中' },
};

export const UploadHistory: React.FC = () => {
  const { t } = useTranslation();
  const [records, setRecords] = useState<UploadHistoryRecord[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const response = await uploadApi.getHistory(20);
      // API returns { status: 'ok', records: [...], total: N }
      setRecords(response.records || []);
    } catch (error) {
      console.error('Failed to fetch upload history:', error);
      setRecords([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const columns = [
    {
      title: t('history.filename'),
      dataIndex: 'original_name',
      key: 'filename',
      ellipsis: true,
      render: (text: string) => (
        <Tooltip title={text}>
          <span>{text}</span>
        </Tooltip>
      ),
    },
    {
      title: t('history.status'),
      dataIndex: 'status',
      key: 'status',
      width: 100,
      align: 'center' as const,
      render: (status: string) => {
        const config = statusConfig[status] || { color: 'default', text: status };
        return (
          <Tag color={config.color}>
            {config.text}
          </Tag>
        );
      },
    },
    {
      title: t('history.size'),
      dataIndex: 'size',
      key: 'size',
      width: 120,
      align: 'right' as const,
      render: (size: number) => formatFileSize(size || 0),
    },
    {
      title: t('history.uploadTime'),
      dataIndex: 'uploaded_at',
      key: 'uploadTime',
      width: 180,
      align: 'center' as const,
      render: (time: string) => formatDateTime(time),
    },
    {
      title: t('history.chunks'),
      dataIndex: 'chunks_created',
      key: 'chunks',
      width: 100,
      align: 'center' as const,
      render: (count: number) => count || 0,
    },
  ];

  return (
    <Card title={t('history.title')}>
      <Table
        dataSource={records}
        columns={columns}
        loading={loading}
        rowKey="id"
        pagination={{ pageSize: 5 }}
        size="small"
        scroll={{ x: 600 }}
      />
    </Card>
  );
};

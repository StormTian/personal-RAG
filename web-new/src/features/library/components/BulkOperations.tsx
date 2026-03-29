import React from 'react';
import { Space, Button, Popconfirm, Typography, Checkbox } from 'antd';
import { DeleteOutlined, ClearOutlined, SelectOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

const { Text } = Typography;

interface BulkOperationsProps {
  selectedCount: number;
  totalCount: number;
  onSelectAll: () => void;
  onDeselectAll: () => void;
  onDeleteSelected: () => void;
  onClearSelection: () => void;
}

export const BulkOperations: React.FC<BulkOperationsProps> = ({
  selectedCount,
  totalCount,
  onSelectAll,
  onDeselectAll,
  onDeleteSelected,
  onClearSelection,
}) => {
  const { t } = useTranslation();

  if (selectedCount === 0) {
    return (
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Text type="secondary">
          {t('files.totalCount', { count: totalCount })}
        </Text>
        <Button
          type="link"
          icon={<SelectOutlined />}
          onClick={onSelectAll}
        >
          {t('files.selectAll')}
        </Button>
      </div>
    );
  }

  return (
    <div
      style={{
        marginBottom: 16,
        padding: 12,
        backgroundColor: '#e6f7ff',
        borderRadius: 8,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}
    >
      <Space>
        <Checkbox checked={selectedCount > 0} indeterminate={selectedCount < totalCount} />
        <Text strong>
          {t('files.selectedCount', { selected: selectedCount, total: totalCount })}
        </Text>
      </Space>

      <Space>
        <Button type="link" onClick={onDeselectAll}>
          {t('files.deselectAll')}
        </Button>
        <Button
          icon={<ClearOutlined />}
          onClick={onClearSelection}
        >
          {t('files.clearSelection')}
        </Button>
        <Popconfirm
          title={t('files.bulkDeleteConfirm', { count: selectedCount })}
          onConfirm={onDeleteSelected}
          okText={t('common.confirm')}
          cancelText={t('common.cancel')}
          okButtonProps={{ danger: true }}
        >
          <Button type="primary" danger icon={<DeleteOutlined />}>
            {t('common.delete')}
          </Button>
        </Popconfirm>
      </Space>
    </div>
  );
};

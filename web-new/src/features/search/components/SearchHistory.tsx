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

import React from 'react';
import { Card, List, Tag, Space, Typography, Button, Empty } from 'antd';
import { StarOutlined, DeleteOutlined, FileTextOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useSearchStore } from '../stores/searchStore';
import { formatDate } from '@/utils/format';

const { Text } = Typography;

interface FavoritesListProps {
  onSelect: (query: string) => void;
}

export const FavoritesList: React.FC<FavoritesListProps> = ({ onSelect }) => {
  const { t } = useTranslation();
  const { favorites, removeFromFavorites } = useSearchStore();

  if (favorites.length === 0) {
    return (
      <Card style={{ marginTop: 24 }}>
        <Empty
          image={<StarOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />}
          description={t('search.noFavorites')}
        />
      </Card>
    );
  }

  return (
    <Card
      title={
        <Space>
          <StarOutlined />
          {t('search.favorites')}
        </Space>
      }
      style={{ marginTop: 24 }}
    >
      <List
        dataSource={favorites}
        renderItem={(item) => (
          <List.Item
            actions={[
              <Button
                type="text"
                icon={<DeleteOutlined />}
                onClick={() => removeFromFavorites(item.id)}
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
              {item.notes && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {item.notes}
                </Text>
              )}
              <Space>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {formatDate(item.createdAt)}
                </Text>
                <Tag icon={<FileTextOutlined />}>
                  {item.hits.length} hits
                </Tag>
              </Space>
            </Space>
          </List.Item>
        )}
      />
    </Card>
  );
};

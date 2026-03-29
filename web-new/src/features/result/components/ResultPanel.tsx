import React, { useMemo } from 'react';
import { Card, Space, Typography, Skeleton, Empty, Alert, Row, Col } from 'antd';
import { useTranslation } from 'react-i18next';
import type { SearchResponse } from '@/types';
import { AnswerCard } from './AnswerCard';
import { ContextCard } from './ContextCard';
import { FavoriteButton } from '@/features/search/components/FavoriteButton';

const { Title } = Typography;

interface ResultPanelProps {
  data?: SearchResponse;
  loading?: boolean;
  error?: Error | null;
  query?: string;
  onRetry?: () => void;
}

export const ResultPanel: React.FC<ResultPanelProps> = ({
  data,
  loading,
  error,
  query,
  onRetry,
}) => {
  const { t } = useTranslation();
  
  const keywords = useMemo(() => {
    if (!query) return [];
    return query.split(/\s+/).filter(w => w.length > 1);
  }, [query]);
  
  if (loading) {
    return (
      <Card title={t('result.title')}>
        <Skeleton active paragraph={{ rows: 8 }} />
      </Card>
    );
  }
  
  if (error) {
    return (
      <Card title={t('result.title')}>
        <Alert
          message={error.message}
          type="error"
          action={onRetry && (
            <button onClick={onRetry}>{t('error.retry')}</button>
          )}
          showIcon
        />
      </Card>
    );
  }
  
  if (!data) {
    return (
      <Card title={t('result.title')}>
        <Empty description={t('status.waiting')} />
      </Card>
    );
  }
  
  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Row justify="space-between" align="middle" style={{ width: '100%' }}>
        <Col flex="auto">
          <AnswerCard lines={data.answer_lines} />
        </Col>
        <Col>
          {query && data.hits.length > 0 && (
            <FavoriteButton query={query} hits={data.hits} />
          )}
        </Col>
      </Row>
      
      <Card title={<Title level={4}>{t('result.contexts')}</Title>}>
        {data.hits.length === 0 ? (
          <Empty description={t('search.noResults')} />
        ) : (
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            {data.hits.map((hit, index) => (
              <ContextCard
                key={`${hit.source}-${index}`}
                hit={hit}
                keywords={keywords}
              />
            ))}
          </Space>
        )}
      </Card>
    </Space>
  );
};

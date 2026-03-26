import React from 'react';
import { Card, Tag, Space, Typography, Tooltip } from 'antd';
import type { SearchHit } from '@/types';
import { formatScore, highlightText } from '@/utils/format';
import { useTranslation } from 'react-i18next';

const { Text } = Typography;

interface ContextCardProps {
  hit: SearchHit;
  keywords?: string[];
}

export const ContextCard: React.FC<ContextCardProps> = ({ hit, keywords }) => {
  const { t } = useTranslation();
  const highlightedText = keywords?.length
    ? highlightText(hit.text, keywords)
    : hit.text;
  
  return (
    <Card
      size="small"
      title={
        <Space>
          <Text strong>{hit.source}</Text>
          <Tooltip title={`Vector: ${formatScore(hit.retrieve_score)}, BM25: ${formatScore(hit.lexical_score)}`}>
            <Tag color="blue">
              {t('result.score')} {formatScore(hit.score)}
            </Tag>
          </Tooltip>
        </Space>
      }
    >
      <div
        dangerouslySetInnerHTML={{ __html: highlightedText }}
        style={{ lineHeight: 1.7 }}
      />
    </Card>
  );
};

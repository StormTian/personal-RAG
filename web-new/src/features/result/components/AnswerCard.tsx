import React from 'react';
import { Card, Typography, Skeleton, Empty } from 'antd';
import { useTranslation } from 'react-i18next';
import { processMarkdown } from '@/utils/highlight';

const { Title } = Typography;

interface AnswerCardProps {
  lines: string[];
  loading?: boolean;
}

export const AnswerCard: React.FC<AnswerCardProps> = ({ lines, loading }) => {
  const { t } = useTranslation();
  
  if (loading) {
    return (
      <Card title={t('result.answer')}>
        <Skeleton active paragraph={{ rows: 6 }} />
      </Card>
    );
  }
  
  if (!lines.length) {
    return (
      <Card title={t('result.answer')}>
        <Empty description={t('search.noAnswer')} />
      </Card>
    );
  }
  
  const markdown = lines.join('\n\n');
  const html = processMarkdown(markdown);
  
  return (
    <Card title={<Title level={4}>{t('result.answer')}</Title>}>
      <div
        className="answer-content markdown-body"
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </Card>
  );
};

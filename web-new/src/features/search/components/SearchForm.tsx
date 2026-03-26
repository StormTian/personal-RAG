import React, { useState, useCallback } from 'react';
import { Form, Input, Button, Card, Space, Typography, InputNumber } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface SearchFormProps {
  onSearch: (query: string, topK: number) => void;
  loading?: boolean;
}

export const SearchForm: React.FC<SearchFormProps> = ({ onSearch, loading }) => {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const [query, setQuery] = useState('');
  
  const handleSubmit = useCallback(() => {
    form.validateFields().then(({ query, topK }) => {
      onSearch(query, topK);
    });
  }, [form, onSearch]);
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.metaKey) {
      handleSubmit();
    }
  };
  
  return (
    <Card
      title={
        <Space>
          <Title level={3} style={{ margin: 0 }}>{t('search.title')}</Title>
          <Text type="secondary" style={{ fontSize: 12, background: 'rgba(153, 88, 42, 0.1)', padding: '2px 8px', borderRadius: 999 }}>
            {t('search.badge')}
          </Text>
        </Space>
      }
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{ topK: 3 }}
        onFinish={handleSubmit}
      >
        <Form.Item
          name="query"
          label={t('search.placeholder')}
          rules={[{ required: true, message: t('error.emptyQuery') }]}
        >
          <TextArea
            rows={4}
            placeholder={t('search.placeholder')}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            autoFocus
          />
        </Form.Item>
        
        <Space align="end" style={{ width: '100%', justifyContent: 'space-between' }}>
          <Form.Item
            name="topK"
            label={t('search.recallCount')}
            style={{ marginBottom: 0 }}
          >
            <InputNumber min={1} max={20} />
          </Form.Item>
          
          <Button
            type="primary"
            icon={<SearchOutlined />}
            onClick={handleSubmit}
            loading={loading}
            size="large"
          >
            {loading ? t('search.buttonLoading') : t('search.button')}
          </Button>
        </Space>
      </Form>
    </Card>
  );
};

import React, { useEffect, useState } from 'react';
import { Card, Statistic, Row, Col, Tag, Timeline, Alert } from 'antd';
import { CheckCircleOutlined, WarningOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { apiClient } from '@/services/api';

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  checks: Record<string, {
    status: string;
    message: string;
    latency_ms: number;
  }>;
}

export const HealthPanel: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const response = await apiClient.get('/health');
        setHealth(response.data);
        setError(null);
      } catch (err) {
        setError('Failed to fetch health status');
      } finally {
        setLoading(false);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <Alert type="error" message={error} />;
  if (!health) return null;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'degraded':
        return <WarningOutlined style={{ color: '#faad14' }} />;
      default:
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'degraded':
        return 'warning';
      default:
        return 'error';
    }
  };

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card title="System Health">
            <Statistic
              title="Overall Status"
              value={health.status.toUpperCase()}
              prefix={getStatusIcon(health.status)}
              valueStyle={{
                color: health.status === 'healthy' ? '#52c41a' : 
                       health.status === 'degraded' ? '#faad14' : '#ff4d4f'
              }}
            />
            <div style={{ marginTop: 16 }}>
              <Tag color="blue">Last Check: {new Date(health.timestamp).toLocaleString()}</Tag>
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="Component Status">
            <Timeline>
              {Object.entries(health.checks).map(([name, check]) => (
                <Timeline.Item
                  key={name}
                  dot={getStatusIcon(check.status)}
                  color={getStatusColor(check.status)}
                >
                  <strong>{name}</strong>: {check.message}
                  {check.latency_ms > 0 && (
                    <div style={{ fontSize: 12, color: '#999' }}>
                      Latency: {check.latency_ms.toFixed(2)}ms
                    </div>
                  )}
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

import React from 'react';
import { Card, Row, Col, Statistic, Divider } from 'antd';
import type { SearchHit } from '@/types';

interface SearchResultChartProps {
  hits: SearchHit[];
}

export const SearchResultChart: React.FC<SearchResultChartProps> = ({ hits }) => {
  if (!hits || hits.length === 0) return null;

  // Calculate statistics
  const scores = hits.map((h) => h.score);
  const avgScore = scores.reduce((a, b) => a + b, 0) / scores.length;
  const maxScore = Math.max(...scores);
  const minScore = Math.min(...scores);

  // Calculate score distribution
  const scoreRanges = [
    { range: '0.9-1.0', count: 0, color: '#52c41a' },
    { range: '0.8-0.9', count: 0, color: '#73d13d' },
    { range: '0.7-0.8', count: 0, color: '#95de64' },
    { range: '0.6-0.7', count: 0, color: '#b7eb8f' },
    { range: '0.5-0.6', count: 0, color: '#d9f7be' },
    { range: '< 0.5', count: 0, color: '#f0f0f0' },
  ];

  hits.forEach((hit) => {
    const score = hit.score;
    if (score >= 0.9) scoreRanges[0].count++;
    else if (score >= 0.8) scoreRanges[1].count++;
    else if (score >= 0.7) scoreRanges[2].count++;
    else if (score >= 0.6) scoreRanges[3].count++;
    else if (score >= 0.5) scoreRanges[4].count++;
    else scoreRanges[5].count++;
  });

  // Calculate source distribution
  const sourceCount: Record<string, number> = {};
  hits.forEach((hit) => {
    const source = hit.source.split('/').pop() || 'Unknown';
    sourceCount[source] = (sourceCount[source] || 0) + 1;
  });

  const sourceData = Object.entries(sourceCount)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 5);

  const maxCount = Math.max(...scoreRanges.map((r) => r.count), 1);

  return (
    <Card title="搜索结果统计" style={{ marginTop: 24 }}>
      <Row gutter={[16, 16]}>
        <Col span={8}>
          <Statistic
            title="平均分数"
            value={avgScore.toFixed(3)}
            precision={3}
            suffix="/ 1.0"
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="最高分数"
            value={maxScore.toFixed(3)}
            precision={3}
            valueStyle={{ color: '#52c41a' }}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="最低分数"
            value={minScore.toFixed(3)}
            precision={3}
            valueStyle={{ color: '#ff4d4f' }}
          />
        </Col>
      </Row>

      <Divider />

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={12}>
          <h4>分数分布</h4>
          <div style={{ marginTop: 16 }}>
            {scoreRanges.map((range, index) => (
              <div
                key={index}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  marginBottom: 8,
                }}
              >
                <span style={{ width: 60, fontSize: 12 }}>{range.range}</span>
                <div
                  style={{
                    flex: 1,
                    height: 20,
                    backgroundColor: '#f0f0f0',
                    borderRadius: 4,
                    marginLeft: 8,
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      width: `${(range.count / maxCount) * 100}%`,
                      height: '100%',
                      backgroundColor: range.color,
                      transition: 'width 0.3s ease',
                    }}
                  />
                </div>
                <span style={{ width: 40, textAlign: 'right', fontSize: 12, marginLeft: 8 }}>
                  {range.count}
                </span>
              </div>
            ))}
          </div>
        </Col>

        <Col xs={24} lg={12}>
          <h4>来源分布 (Top 5)</h4>
          <div style={{ marginTop: 16 }}>
            {sourceData.map((source, index) => {
              const maxSourceCount = sourceData[0]?.value || 1;
              const colors = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1'];
              return (
                <div
                  key={index}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    marginBottom: 8,
                  }}
                >
                  <span
                    style={{
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      backgroundColor: colors[index % colors.length],
                      marginRight: 8,
                    }}
                  />
                  <span
                    style={{
                      width: 150,
                      fontSize: 12,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                    title={source.name}
                  >
                    {source.name}
                  </span>
                  <div
                    style={{
                      flex: 1,
                      height: 20,
                      backgroundColor: '#f0f0f0',
                      borderRadius: 4,
                      marginLeft: 8,
                      overflow: 'hidden',
                    }}
                  >
                    <div
                      style={{
                        width: `${(source.value / maxSourceCount) * 100}%`,
                        height: '100%',
                        backgroundColor: colors[index % colors.length],
                        transition: 'width 0.3s ease',
                      }}
                    />
                  </div>
                  <span style={{ width: 40, textAlign: 'right', fontSize: 12, marginLeft: 8 }}>
                    {source.value}
                  </span>
                </div>
              );
            })}
          </div>
        </Col>
      </Row>
    </Card>
  );
};

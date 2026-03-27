import React from 'react';
import { Spin } from 'antd';

export const PageLoader: React.FC = () => {
  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center',
      minHeight: '200px',
      padding: '100px 0'
    }}>
      <Spin size="large" />
    </div>
  );
};
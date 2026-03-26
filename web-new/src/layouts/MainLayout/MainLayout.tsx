import React from 'react';
import { Layout, ConfigProvider, theme as antTheme } from 'antd';
import { ThemeToggle } from '@/components/ThemeToggle/ThemeToggle';
import { useThemeStore } from '@/stores/themeStore';
import { lightTheme, darkTheme } from '@/styles/theme';

const { Header, Content } = Layout;

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const { isDark } = useThemeStore();
  
  return (
    <ConfigProvider
      theme={{
        algorithm: isDark ? antTheme.darkAlgorithm : antTheme.defaultAlgorithm,
        ...isDark ? darkTheme : lightTheme,
      }}
    >
      <div className={isDark ? 'dark' : 'light'}>
        <Layout style={{ minHeight: '100vh' }}>
          <Header
            style={{
              display: 'flex',
              justifyContent: 'flex-end',
              alignItems: 'center',
              padding: '0 24px',
              background: 'transparent',
            }}
          >
            <ThemeToggle />
          </Header>
          <Content style={{ padding: '0 24px 48px' }}>
            {children}
          </Content>
        </Layout>
      </div>
    </ConfigProvider>
  );
};

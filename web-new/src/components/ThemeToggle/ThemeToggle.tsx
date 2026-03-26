import React from 'react';
import { Button, Tooltip } from 'antd';
import { MoonOutlined, SunOutlined } from '@ant-design/icons';
import { useThemeStore } from '@/stores/themeStore';
import { useTranslation } from 'react-i18next';

export const ThemeToggle: React.FC = () => {
  const { isDark, toggleMode } = useThemeStore();
  const { t } = useTranslation();
  
  return (
    <Tooltip title={t(isDark ? 'theme.light' : 'theme.dark')}>
      <Button
        type="text"
        icon={isDark ? <SunOutlined /> : <MoonOutlined />}
        onClick={toggleMode}
        aria-label={t(isDark ? 'theme.light' : 'theme.dark')}
      />
    </Tooltip>
  );
};

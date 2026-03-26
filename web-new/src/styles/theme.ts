import type { ThemeConfig } from 'antd';

export const lightTheme: ThemeConfig = {
  token: {
    colorPrimary: '#99582a',
    colorBgBase: '#f5efe6',
    colorTextBase: '#1f1a17',
    colorBorder: 'rgba(95, 72, 47, 0.18)',
    borderRadius: 12,
    fontFamily: '"Avenir Next", "Trebuchet MS", -apple-system, BlinkMacSystemFont, sans-serif',
  },
  components: {
    Button: {
      borderRadius: 999,
    },
    Card: {
      borderRadius: 18,
    },
    Input: {
      borderRadius: 18,
    },
  },
};

export const darkTheme: ThemeConfig = {
  token: {
    colorPrimary: '#c97d60',
    colorBgBase: '#1a1614',
    colorTextBase: '#e8e4e0',
    colorBorder: 'rgba(255, 255, 255, 0.12)',
    borderRadius: 12,
    fontFamily: '"Avenir Next", "Trebuchet MS", -apple-system, BlinkMacSystemFont, sans-serif',
  },
  components: {
    Button: {
      borderRadius: 999,
    },
    Card: {
      borderRadius: 18,
      colorBgContainer: '#2a2522',
    },
    Input: {
      borderRadius: 18,
      colorBgContainer: '#2a2522',
    },
  },
};

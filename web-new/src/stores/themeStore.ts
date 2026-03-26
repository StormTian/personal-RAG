import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ThemeMode } from '@/types';

interface ThemeState {
  mode: ThemeMode;
  isDark: boolean;
  setMode: (mode: ThemeMode) => void;
  toggleMode: () => void;
}

const getIsDark = (mode: ThemeMode): boolean => {
  if (mode === 'system') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  return mode === 'dark';
};

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      mode: 'system',
      isDark: getIsDark('system'),
      
      setMode: (mode) => {
        set({ mode, isDark: getIsDark(mode) });
      },
      
      toggleMode: () => {
        const currentMode = get().mode;
        const newMode: ThemeMode = currentMode === 'dark' ? 'light' : 'dark';
        set({ mode: newMode, isDark: getIsDark(newMode) });
      },
    }),
    {
      name: 'theme-storage',
      onRehydrateStorage: () => (state) => {
        if (state) {
          state.isDark = getIsDark(state.mode);
        }
      },
    }
  )
);

// Listen for system theme changes
if (typeof window !== 'undefined') {
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    const state = useThemeStore.getState();
    if (state.mode === 'system') {
      useThemeStore.setState({ isDark: e.matches });
    }
  });
}

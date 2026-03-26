import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { SearchHistoryItem } from '@/types';

interface SearchState {
  history: SearchHistoryItem[];
  addToHistory: (query: string, hitCount: number) => void;
  clearHistory: () => void;
  removeFromHistory: (id: string) => void;
}

const MAX_HISTORY = 20;

const generateId = () => {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
};

export const useSearchStore = create<SearchState>()(
  persist(
    (set, get) => ({
      history: [],
      
      addToHistory: (query, hitCount) => {
        const { history } = get();
        const newItem: SearchHistoryItem = {
          id: generateId(),
          query,
          timestamp: Date.now(),
          hitCount,
        };
        
        set({
          history: [newItem, ...history.filter(h => h.query !== query)].slice(0, MAX_HISTORY),
        });
      },
      
      clearHistory: () => set({ history: [] }),
      
      removeFromHistory: (id) => {
        const { history } = get();
        set({ history: history.filter(h => h.id !== id) });
      },
    }),
    {
      name: 'search-history',
    }
  )
);

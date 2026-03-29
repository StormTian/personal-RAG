import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { SearchHistoryItem, FavoriteItem, SearchHit } from '@/types';

interface SearchState {
  // History
  history: SearchHistoryItem[];
  addToHistory: (query: string, hitCount: number) => void;
  clearHistory: () => void;
  removeFromHistory: (id: string) => void;
  
  // Favorites
  favorites: FavoriteItem[];
  addToFavorites: (query: string, hits: SearchHit[], notes?: string) => void;
  removeFromFavorites: (id: string) => void;
  updateFavoriteNotes: (id: string, notes: string) => void;
  isFavorited: (query: string) => boolean;
  getFavoriteByQuery: (query: string) => FavoriteItem | undefined;
}

const MAX_HISTORY = 50;
const MAX_FAVORITES = 100;

const generateId = () => {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
};

export const useSearchStore = create<SearchState>()(
  persist(
    (set, get) => ({
      history: [],
      favorites: [],
      
      // History actions
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
      
      // Favorites actions
      addToFavorites: (query, hits, notes) => {
        const { favorites } = get();
        
        // Check if already favorited
        if (favorites.some(f => f.query === query)) {
          return;
        }
        
        const newItem: FavoriteItem = {
          id: generateId(),
          query,
          hits,
          createdAt: Date.now(),
          notes,
        };
        
        set({
          favorites: [...favorites, newItem].slice(0, MAX_FAVORITES),
        });
      },
      
      removeFromFavorites: (id) => {
        const { favorites } = get();
        set({ favorites: favorites.filter(f => f.id !== id) });
      },
      
      updateFavoriteNotes: (id, notes) => {
        const { favorites } = get();
        set({
          favorites: favorites.map(f =>
            f.id === id ? { ...f, notes } : f
          ),
        });
      },
      
      isFavorited: (query) => {
        const { favorites } = get();
        return favorites.some(f => f.query === query);
      },
      
      getFavoriteByQuery: (query) => {
        const { favorites } = get();
        return favorites.find(f => f.query === query);
      },
    }),
    {
      name: 'search-storage',
    }
  )
);

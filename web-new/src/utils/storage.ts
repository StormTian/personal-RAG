const STORAGE_PREFIX = 'rag_demo_';

export const storage = {
  get<T>(key: string, defaultValue?: T): T | undefined {
    try {
      const item = localStorage.getItem(`${STORAGE_PREFIX}${key}`);
      return item ? JSON.parse(item) : defaultValue;
    } catch {
      return defaultValue;
    }
  },
  
  set<T>(key: string, value: T): void {
    try {
      localStorage.setItem(`${STORAGE_PREFIX}${key}`, JSON.stringify(value));
    } catch {
      console.warn('localStorage set failed');
    }
  },
  
  remove(key: string): void {
    localStorage.removeItem(`${STORAGE_PREFIX}${key}`);
  },
  
  clear(): void {
    Object.keys(localStorage)
      .filter(key => key.startsWith(STORAGE_PREFIX))
      .forEach(key => localStorage.removeItem(key));
  },
};

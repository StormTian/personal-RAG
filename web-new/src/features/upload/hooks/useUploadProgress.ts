import { useState, useCallback, useRef } from 'react';

export interface UploadFile {
  id: string;
  file: File;
  name: string;
  size: number;
  progress: number;
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
  speed?: number; // bytes per second
}

export interface UseUploadProgressReturn {
  uploads: UploadFile[];
  addFiles: (files: File[]) => void;
  updateProgress: (id: string, progress: number, bytesUploaded?: number) => void;
  markSuccess: (id: string) => void;
  markError: (id: string, error: string) => void;
  clearCompleted: () => void;
  clearAll: () => void;
  hasActiveUploads: boolean;
  hasCompletedUploads: boolean;
}

const generateId = () => {
  return Math.random().toString(36).substring(2, 15);
};

export const useUploadProgress = (): UseUploadProgressReturn => {
  const [uploads, setUploads] = useState<UploadFile[]>([]);
  const uploadStartTimes = useRef<Record<string, number>>({});

  const addFiles = useCallback((files: File[]) => {
    const newUploads: UploadFile[] = files.map((file) => {
      const id = generateId();
      uploadStartTimes.current[id] = Date.now();
      return {
        id,
        file,
        name: file.name,
        size: file.size,
        progress: 0,
        status: 'pending',
      };
    });

    setUploads((prev) => [...prev, ...newUploads]);
  }, []);

  const updateProgress = useCallback((id: string, progress: number, bytesUploaded?: number) => {
    setUploads((prev) =>
      prev.map((upload) => {
        if (upload.id !== id) return upload;

        let speed: number | undefined;
        if (bytesUploaded && uploadStartTimes.current[id]) {
          const elapsed = (Date.now() - uploadStartTimes.current[id]) / 1000;
          if (elapsed > 0) {
            speed = bytesUploaded / elapsed;
          }
        }

        return {
          ...upload,
          progress,
          status: 'uploading',
          speed,
        };
      })
    );
  }, []);

  const markSuccess = useCallback((id: string) => {
    setUploads((prev) =>
      prev.map((upload) =>
        upload.id === id
          ? { ...upload, status: 'success', progress: 100 }
          : upload
      )
    );
    delete uploadStartTimes.current[id];
  }, []);

  const markError = useCallback((id: string, error: string) => {
    setUploads((prev) =>
      prev.map((upload) =>
        upload.id === id ? { ...upload, status: 'error', error } : upload
      )
    );
    delete uploadStartTimes.current[id];
  }, []);

  const clearCompleted = useCallback(() => {
    setUploads((prev) => {
      const active = prev.filter(
        (u) => u.status === 'pending' || u.status === 'uploading'
      );
      // Clean up refs for completed uploads
      prev
        .filter((u) => u.status === 'success' || u.status === 'error')
        .forEach((u) => delete uploadStartTimes.current[u.id]);
      return active;
    });
  }, []);

  const clearAll = useCallback(() => {
    setUploads([]);
    uploadStartTimes.current = {};
  }, []);

  const hasActiveUploads = uploads.some(
    (u) => u.status === 'pending' || u.status === 'uploading'
  );

  const hasCompletedUploads = uploads.some(
    (u) => u.status === 'success' || u.status === 'error'
  );

  return {
    uploads,
    addFiles,
    updateProgress,
    markSuccess,
    markError,
    clearCompleted,
    clearAll,
    hasActiveUploads,
    hasCompletedUploads,
  };
};

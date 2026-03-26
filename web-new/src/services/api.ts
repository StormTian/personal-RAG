import { apiClient } from './client';
import type {
  LibraryInfo,
  SearchResponse,
  SearchParams,
  UploadResponse,
  FileListResponse,
  DeleteFileResponse,
  UploadHistoryResponse,
  UploadProgressCallback,
} from '@/types';

// 文档库相关 API
export const libraryApi = {
  async getInfo(): Promise<LibraryInfo> {
    return apiClient.get<LibraryInfo>('/api/library');
  },
  
  async reload(): Promise<LibraryInfo> {
    return apiClient.post<LibraryInfo>('/api/reload');
  },
};

// 搜索相关 API
export const searchApi = {
  async query(params: SearchParams): Promise<SearchResponse> {
    return apiClient.post<SearchResponse>('/api/ask', params);
  },
};

// 文件上传相关 API
export const uploadApi = {
  /**
   * 上传文件
   * @param file 文件对象
   * @param onProgress 进度回调函数
   * @param autoReload 上传后是否自动重新加载 RAG 索引
   * @returns 上传响应
   */
  async uploadFile(
    file: File,
    onProgress?: UploadProgressCallback,
    autoReload: boolean = true
  ): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('auto_reload', String(autoReload));

    return apiClient.post<UploadResponse>('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: onProgress
        ? (progressEvent) => {
            if (progressEvent.total) {
              const percentage = Math.round(
                (progressEvent.loaded * 100) / progressEvent.total
              );
              onProgress({
                loaded: progressEvent.loaded,
                total: progressEvent.total,
                percentage,
              });
            }
          }
        : undefined,
    });
  },

  /**
   * 获取上传历史记录
   * @param limit 返回记录数量限制
   * @param offset 偏移量
   * @returns 上传历史响应
   */
  async getHistory(
    limit: number = 50,
    offset: number = 0
  ): Promise<UploadHistoryResponse> {
    return apiClient.get<UploadHistoryResponse>('/api/upload-history', {
      params: { limit, offset },
    });
  },
};

// 文件管理相关 API
export const filesApi = {
  /**
   * 获取文件列表
   * @returns 文件列表响应
   */
  async listFiles(): Promise<FileListResponse> {
    return apiClient.get<FileListResponse>('/api/files');
  },

  /**
   * 删除文件
   * @param filename 文件名（原始名称或存储名称）
   * @returns 删除响应
   */
  async deleteFile(filename: string): Promise<DeleteFileResponse> {
    return apiClient.delete<DeleteFileResponse>(`/api/files/${encodeURIComponent(filename)}`);
  },
};

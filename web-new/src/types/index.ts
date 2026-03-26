// API 响应类型
export interface ApiResponse<T = unknown> {
  data: T;
  success: boolean;
  message?: string;
}

export interface ApiError {
  error: string;
  code?: number;
}

// 文档库类型
export interface LibraryInfo {
  documents: number;
  chunks: number;
  supported_formats: string[];
  embedding_backend: string;
  reranker_backend: string;
  retrieval_strategy: string;
  rerank_strategy: string;
  files: LibraryFile[];
  skipped: SkippedFile[];
}

export interface LibraryFile {
  source: string;
  title: string;
  file_type: string;
  chars: number;
}

export interface SkippedFile {
  source: string;
  error: string;
}

// 搜索结果类型
export interface SearchHit {
  source: string;
  text: string;
  score: number;
  retrieve_score: number;
  lexical_score: number;
}

export interface SearchResponse {
  answer_lines: string[];
  hits: SearchHit[];
  query_time?: number;
}

export interface SearchParams {
  query: string;
  top_k: number;
}

// 主题类型
export type ThemeMode = 'light' | 'dark' | 'system';

// 搜索历史
export interface SearchHistoryItem {
  id: string;
  query: string;
  timestamp: number;
  hitCount: number;
}

// ==================== 上传相关类型 ====================

/**
 * 上传文件响应
 */
export interface UploadResponse {
  status: string;
  message: string;
  file: {
    original_name: string;
    saved_name: string;
    path: string;
    size: number;
    type: string;
  };
  reloaded: boolean;
  library_stats?: {
    documents: number;
    chunks: number;
    supported_formats: string[];
  };
}

/**
 * 文件信息
 */
export interface FileInfoResponse {
  file_id: string;
  original_name: string;
  stored_name: string;
  file_path: string;
  file_size: number;
  file_size_human: string;
  file_type: string;
  created_at: string;
  metadata: Record<string, unknown>;
}

/**
 * 文件列表响应
 */
export interface FileListResponse {
  files: FileInfoResponse[];
  total: number;
}

/**
 * 删除文件响应
 */
export interface DeleteFileResponse {
  success: boolean;
  message: string;
  filename: string;
}

/**
 * 上传状态
 */
export type UploadStatus = 'success' | 'failed' | 'pending' | 'deleted';

/**
 * 上传历史记录
 */
export interface UploadHistoryRecord {
  id: number;
  original_name: string;
  saved_name: string;
  size: number;
  type: string;
  status: UploadStatus;
  uploaded_at: string;
  auto_reloaded: boolean;
  chunks_created: number;
}

/**
 * 上传历史响应
 */
export interface UploadHistoryResponse {
  status: string;
  records: UploadHistoryRecord[];
  total: number;
}

// ==================== 上传进度相关类型 ====================

/**
 * 上传进度回调函数类型
 */
export type UploadProgressCallback = (progress: UploadProgressEvent) => void;

/**
 * 上传进度事件
 */
export interface UploadProgressEvent {
  loaded: number;
  total: number;
  percentage: number;
}

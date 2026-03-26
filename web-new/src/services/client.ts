import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

class ApiClient {
  private client: AxiosInstance;
  
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    this.setupInterceptors();
  }
  
  private setupInterceptors(): void {
    this.client.interceptors.request.use(
      (config) => config,
      (error) => Promise.reject(error)
    );
    
    this.client.interceptors.response.use(
      (response) => response.data,
      (error: AxiosError<{ error?: string }>) => {
        const message = error.response?.data?.error || error.message || '请求失败';
        return Promise.reject(new Error(message));
      }
    );
  }
  
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.client.get(url, config);
  }
  
  async post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return this.client.post(url, data, config);
  }
  
  async put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return this.client.put(url, data, config);
  }
  
  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.client.delete(url, config);
  }
}

export const apiClient = new ApiClient();

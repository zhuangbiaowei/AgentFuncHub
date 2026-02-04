/**
 * API 客户端
 */

import { FunctionSpec, SearchResponse, User, Token, ExecutionResult } from './types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }

  getToken(): string | null {
    if (!this.token) {
      this.token = localStorage.getItem('token');
    }
    return this.token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options.headers as Record<string, string>) || {}),
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // === 函数 API ===
  async listFunctions(params?: { language?: string; tag?: string; limit?: number }): Promise<{
    success: boolean;
    total: number;
    functions: FunctionSpec[];
  }> {
    const query = new URLSearchParams();
    if (params?.language) query.append('language', params.language);
    if (params?.tag) query.append('tag', params.tag);
    if (params?.limit) query.append('limit', params.limit.toString());

    return this.request(`/functions?${query.toString()}`);
  }

  async getFunction(id: string): Promise<{ success: boolean; function: FunctionSpec }> {
    return this.request(`/functions/${id}`);
  }

  async searchFunctions(query: string, limit: number = 10): Promise<SearchResponse> {
    return this.request('/search', {
      method: 'POST',
      body: JSON.stringify({ query, limit }),
    });
  }

  async executeFunction(id: string, input: Record<string, any>): Promise<ExecutionResult> {
    return this.request(`/execute/functions/${id}`, {
      method: 'POST',
      body: JSON.stringify(input),
    });
  }

  async createFunction(spec: FunctionSpec): Promise<{ success: boolean; function_id: string }> {
    return this.request('/functions', {
      method: 'POST',
      body: JSON.stringify(spec),
    });
  }

  // === 认证 API ===
  async getCurrentUser(): Promise<User> {
    return this.request('/auth/me');
  }

  async createApiKey(): Promise<{ api_key: string; message: string }> {
    return this.request('/auth/api-keys', { method: 'POST' });
  }

  // === 元数据 API ===
  async getTags(): Promise<{ tags: string[] }> {
    return this.request('/tags');
  }

  async getLanguages(): Promise<{ languages: string[] }> {
    return this.request('/languages');
  }
}

export const api = new ApiClient();

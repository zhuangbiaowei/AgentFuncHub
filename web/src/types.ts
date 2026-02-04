/**
 * API 类型定义
 */

export interface FunctionSpec {
  spec_version: string;
  id: string;
  version: string;
  name: string;
  description: string;
  license?: string;
  language: {
    name: string;
    runtime?: string;
  };
  entrypoint: {
    kind: string;
    symbol: string;
    code?: string;
  };
  signature: {
    inputs: Record<string, ParameterSchema>;
    outputs: Record<string, ParameterSchema>;
  };
  semantics?: {
    deterministic: boolean;
    side_effects: string[];
    purity: string;
  };
  tags?: string[];
  quality?: {
    maturity: string;
    coverage: number;
  };
}

export interface ParameterSchema {
  type: string;
  required: boolean;
  description?: string;
  example?: any;
  default?: any;
}

export interface FunctionSearchResult {
  function_id: string;
  name: string;
  description: string;
  similarity_score: number;
  spec: FunctionSpec;
}

export interface SearchResponse {
  success: boolean;
  query: string;
  total: number;
  results: FunctionSearchResult[];
}

export interface User {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  is_active: boolean;
  created_at: string;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface ExecutionResult {
  result?: any;
  error?: string;
  duration_ms?: number;
}

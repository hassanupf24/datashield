/**
 * DATASHIELD API Client
 * Type-safe HTTP client for backend communication.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ApiOptions {
  method?: string;
  body?: any;
  token?: string;
  headers?: Record<string, string>;
}

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  setToken(token: string) {
    this.token = token;
  }

  clearToken() {
    this.token = null;
  }

  private async request<T>(endpoint: string, options: ApiOptions = {}): Promise<T> {
    const { method = 'GET', body, token, headers = {} } = options;

    const authToken = token || this.token;
    const requestHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...headers,
    };

    if (authToken) {
      requestHeaders['Authorization'] = `Bearer ${authToken}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method,
      headers: requestHeaders,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return response.json();
  }

  // Auth
  async login(username: string, password: string) {
    const data = await this.request<any>('/api/v1/auth/login', {
      method: 'POST',
      body: { username, password },
    });
    this.setToken(data.access_token);
    return data;
  }

  async getMe() {
    return this.request<any>('/api/v1/auth/me');
  }

  // Dashboard
  async getDashboardStats() {
    return this.request<any>('/api/v1/dashboard/stats');
  }

  async getComplianceOverview() {
    return this.request<any>('/api/v1/dashboard/compliance');
  }

  async getRecentAlerts(limit = 20) {
    return this.request<any>(`/api/v1/dashboard/alerts?limit=${limit}`);
  }

  // Assets
  async getAssets(params?: Record<string, string>) {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return this.request<any>(`/api/v1/assets${query}`);
  }

  async getAsset(id: string) {
    return this.request<any>(`/api/v1/assets/${id}`);
  }

  // Events
  async getEvents(params?: Record<string, string>) {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return this.request<any>(`/api/v1/tracking/events${query}`);
  }

  // Lineage
  async getLineageGraph(assetId: string, depth = 3) {
    return this.request<any>(`/api/v1/lineage/graph/${assetId}?depth=${depth}`);
  }

  async getImpactAnalysis(assetId: string) {
    return this.request<any>(`/api/v1/lineage/impact/${assetId}`);
  }

  // Policies
  async getPolicies(params?: Record<string, string>) {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return this.request<any>(`/api/v1/policies${query}`);
  }

  // Audit
  async getAuditLogs(params?: Record<string, string>) {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return this.request<any>(`/api/v1/audit/logs${query}`);
  }

  async verifyAuditChain() {
    return this.request<any>('/api/v1/audit/verify-chain');
  }

  // Classification
  async classifyData(assetId: string, sampleData: string[], language = 'en') {
    return this.request<any>('/api/v1/classification/analyze', {
      method: 'POST',
      body: { asset_id: assetId, sample_data: sampleData, language },
    });
  }

  // Health
  async getHealth() {
    return this.request<any>('/health');
  }
}

export const api = new ApiClient(API_BASE);
export default api;

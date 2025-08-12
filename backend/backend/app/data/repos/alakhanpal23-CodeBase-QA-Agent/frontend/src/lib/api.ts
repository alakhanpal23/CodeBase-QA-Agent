import { Repository, QueryRequest, QueryResponse, IngestRequest } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export const api = {
  async getRepos(): Promise<Repository[]> {
    const response = await fetch(`${API_BASE_URL}/repos`);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const error = new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      (error as any).response = { data: errorData };
      throw error;
    }
    return response.json();
  },

  async ingestRepo(data: IngestRequest): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/ingest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const error = new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      (error as any).response = { data: errorData };
      throw error;
    }
    return response.json();
  },

  async deleteRepo(repoId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/repos/${repoId}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const error = new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      (error as any).response = { data: errorData };
      throw error;
    }
  },

  async query(data: QueryRequest): Promise<QueryResponse> {
    const response = await fetch(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const error = new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      (error as any).response = { data: errorData };
      throw error;
    }
    return response.json();
  },
};
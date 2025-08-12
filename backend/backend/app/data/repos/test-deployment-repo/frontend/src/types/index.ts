export interface Repository {
  repo_id: string;
  name: string;
  file_count: number;
  chunk_count: number;
}

export interface Citation {
  path: string;
  start: number;
  end: number;
  score: number;
}

export interface Snippet {
  path: string;
  start: number;
  end: number;
  window_start: number;
  window_end: number;
  code: string;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  snippets: Snippet[];
  latency_ms: number;
  mode?: string;
  confidence?: number;
}

export interface QueryRequest {
  question: string;
  repo_ids: string[];
  k?: number;
}

export interface IngestRequest {
  repo_url?: string;
}

export interface ChatMessage {
  id: string;
  question: string;
  response?: QueryResponse;
  timestamp: number;
  isLoading?: boolean;
}
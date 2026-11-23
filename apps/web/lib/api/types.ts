export type DocumentRow = {
  document_id: string;
  name: string;
  doc_type: string;
  module: string | null;
  version_id: string;
  version: number;
  status: string;
  chunk_count: number;
  error: string | null;
};

export type JobRow = {
  job_id: string;
  status: string;
  progress: number;
  error: string | null;
  chunk_count: number;
};

export type SourceHit = {
  chunk_id: string;
  score: number;
  section_path: string[];
  loc: Record<string, number>;
  document_name: string;
  text: string;
};

export type ClaimSource = {
  chunk_id: string;
  document_name: string;
  section_path: string[];
  loc: Record<string, number>;
};

export type Claim = {
  text: string;
  chunk_ids: string[];
  status: string;
  sources: ClaimSource[];
};

export type FinalAnswer = {
  insufficient_evidence: boolean;
  answer: string;
  claims: Claim[];
  notes: string;
};

export type Usage = {
  tokens_in: number;
  tokens_out: number;
  prompt_version: string;
  latency_ms: number;
};

export type ApiErrorBody = {
  code: string;
  message: string;
};

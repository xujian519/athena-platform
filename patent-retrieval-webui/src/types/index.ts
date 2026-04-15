export interface RetrievalResult {
  patent_id: string;
  title: string;
  abstract: string;
  score: number;
  source: 'fulltext' | 'vector' | 'kg';
  evidence: string;
  metadata: {
    highlight?: {
      title: string;
      abstract: string;
    };
    rank_breakdown?: {
      title_rank: number;
      abstract_rank: number;
    };
    vector_id?: string;
    vector_score?: number;
    tech_count?: number;
    citation_count?: number;
    matched_tech?: string[];
    matched_ipc?: string[];
    sources: string[];
    score_breakdown?: {
      fulltext: number;
      vector: number;
      kg: number;
      weights: {
        fulltext: number;
        vector: number;
        kg: number;
      };
    };
  };
}

export interface PatentDocument {
  patent_id: string;
  title: string;
  abstract: string;
  claims: string;
  description: string;
  ipc_codes: string[];
  publication_date: string;
  applicant: string;
  inventors: string[];
  citations: string[];
  family_id?: string;
  priority_date?: string;
  legal_status?: string;
}

export interface PatentDetails {
  basic_info: PatentDocument;
  knowledge_graph: {
    technologies: string[];
    citations_made: number;
    citations_received: number;
    ipc_codes: string[];
    family_ids: string[];
  };
  retrieval_stats: {
    last_accessed: string;
    data_source: string;
  };
}

export interface SearchRequest {
  query: string;
  top_k?: number;
  filters?: {
    ipc_codes?: string[];
    applicant?: string;
    date_range?: {
      start: string;
      end: string;
    };
  };
}

export interface SearchResponse {
  results: RetrievalResult[];
  query_time: number;
  total_results: number;
  sources: {
    fulltext: number;
    vector: number;
    kg: number;
  };
}

export interface SystemStats {
  components: {
    postgresql: boolean;
    qdrant: boolean;
    neo4j: boolean;
  };
  patent_count: number;
  weights: {
    fulltext: number;
    vector: number;
    kg: number;
  };
  last_updated: string;
}

export interface ConfigWeights {
  fulltext: number;
  vector: number;
  kg: number;
}

export interface SearchHistory {
  id: string;
  query: string;
  timestamp: string;
  results_count: number;
  results?: RetrievalResult[];
}

export interface MonitoringMetrics {
  cache_hit_rate: number;
  avg_response_time: number;
  active_connections: number;
  error_rate: number;
  queries_per_minute: number;
}

import type {
  MacroIndicator,
  TrendAnalysis,
  AnomalyEvent,
  PolicyTargetGap,
  NewsSentimentArticle,
  ResearchDoc,
  GeneratedReport,
  DataSourceStatus,
  IngestionJob,
  SystemHealth,
  EmergingProblem,
  ProblemDetail,
  SystemAlert,
} from './types';

const rawBase = import.meta.env.VITE_API_URL || '';
export const API_BASE = rawBase ? `${rawBase.replace(/\/$/, '')}/api/v1` : '/api/v1';

async function fetchJSON<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, options);
  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`API Error [${response.status}]: ${errorBody || response.statusText}`);
  }
  return response.json();
}

export const api = {
  // Auth & Admin User Provisioning
  getUsers: async (): Promise<Array<{ id: string; email: string; full_name: string; role: string; is_active: boolean }>> => {
    return fetchJSON('/auth/users');
  },
  adminCreateUser: async (data: { email: string; password: string; full_name: string; role: string }) => {
    const response = await fetch(`${API_BASE}/auth/admin/create-user`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const err = await response.text();
      throw new Error(`User provisioning failed: ${err}`);
    }
    return await response.json();
  },
  adminUpdateUserRole: async (userId: string, role: string) => {
    const response = await fetch(`${API_BASE}/auth/admin/users/${userId}/role`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role }),
    });
    if (!response.ok) throw new Error('Role update failed');
    return await response.json();
  },

  // Indicators (Real SBP/PBS Time-Series)
  getIndicators: async (): Promise<MacroIndicator[]> => {
    return fetchJSON<MacroIndicator[]>('/indicators/');
  },
  getIndicatorByCode: async (code: string): Promise<MacroIndicator> => {
    return fetchJSON<MacroIndicator>(`/indicators/${code}`);
  },
  getIndicatorHistory: async (code: string): Promise<Array<{ date: string; value: number; benchmark?: number }>> => {
    const raw = await fetchJSON<
      | Array<{ observation_date?: string; timestamp?: string; value: number }>
      | { history: Array<{ date?: string; observation_date?: string; timestamp?: string; value: number }>; benchmark?: { target_value?: number } }
    >(`/indicators/${code}/history`);

    // Backend returns { history: [...], benchmark: {...} } — unwrap it
    const items = Array.isArray(raw) ? raw : ((raw as any).history || []);
    const benchmarkVal: number | undefined =
      !Array.isArray(raw) && (raw as any).benchmark?.target_value !== undefined
        ? Number((raw as any).benchmark.target_value)
        : undefined;

    return (items as any[]).map((item: any, idx: number) => ({
      date: item.date || item.observation_date || (item.timestamp ? item.timestamp.substring(0, 7) : `T-${idx}`),
      value: Number(item.value),
      ...(benchmarkVal !== undefined ? { benchmark: benchmarkVal } : {}),
    }));
  },

  // Trends & Analytics (Real ML IsolationForest & Moving Avg)
  getTrends: async (timeframe: string = 'all'): Promise<TrendAnalysis[]> => {
    const res = await fetchJSON<TrendAnalysis[] | { trends: TrendAnalysis[] }>(`/trends/?timeframe=${timeframe}`);
    return Array.isArray(res) ? res : (res.trends || []);
  },
  getAnomalies: async (): Promise<AnomalyEvent[]> => {
    return fetchJSON<AnomalyEvent[]>('/anomalies/');
  },

  // Emerging Economic Problems
  getProblems: async (): Promise<EmergingProblem[]> => {
    return fetchJSON<EmergingProblem[]>('/problems/');
  },
  getProblemDetail: async (id: string): Promise<ProblemDetail> => {
    return fetchJSON<ProblemDetail>(`/problems/${id}`);
  },

  // Alerts
  getAlerts: async (): Promise<SystemAlert[]> => {
    return fetchJSON<SystemAlert[]>('/alerts/');
  },

  // Policy Target Gaps (Real Statutory Target Benchmark Analysis)
  getPolicyGaps: async (): Promise<PolicyTargetGap[]> => {
    return fetchJSON<PolicyTargetGap[]>('/policy/gaps');
  },

  // News & Sentiment (Real RSS/Media Ingestion)
  getNews: async (): Promise<NewsSentimentArticle[]> => {
    return fetchJSON<NewsSentimentArticle[]>('/news/');
  },

  // Research Papers (Real PIDE Research Showcase DB & RAG)
  getResearchPapers: async (): Promise<ResearchDoc[]> => {
    return fetchJSON<ResearchDoc[]>('/research/');
  },
  uploadResearchPaper: async (formData: FormData): Promise<{ message: string; doc_id: string; document_identifier?: string }> => {
    const response = await fetch(`${API_BASE}/research/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Upload failed: ${err}`);
    }
    return await response.json();
  },

  // Reports (Real DB & OpenRouter LLM)
  getReports: async (): Promise<GeneratedReport[]> => {
    return fetchJSON<GeneratedReport[]>('/reports/');
  },
  getReportDetail: async (id: string): Promise<GeneratedReport> => {
    return fetchJSON<GeneratedReport>(`/reports/${id}`);
  },
  generateReport: async (): Promise<{ message: string }> => {
    const response = await fetch(`${API_BASE}/reports/generate`, { method: 'POST' });
    if (!response.ok) throw new Error('Report Generation Failed');
    return await response.json();
  },
  deleteReport: async (id: string): Promise<{ message: string }> => {
    const response = await fetch(`${API_BASE}/reports/${id}`, { method: 'DELETE' });
    if (!response.ok) throw new Error('Report Deletion Failed');
    return await response.json();
  },

  // Admin & System (Real DB & Connectors)
  getDataSources: async (): Promise<DataSourceStatus[]> => {
    return fetchJSON<DataSourceStatus[]>('/admin/ingestion/sources');
  },
  getIngestionJobs: async (): Promise<IngestionJob[]> => {
    return fetchJSON<IngestionJob[]>('/admin/ingestion/jobs');
  },
  getSystemHealth: async (): Promise<SystemHealth> => {
    return fetchJSON<SystemHealth>('/health/db');
  },
  triggerIngestion: async (sourceId: string): Promise<{ message: string; result: unknown }> => {
    const response = await fetch(`${API_BASE}/admin/ingestion/${encodeURIComponent(sourceId)}/run`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Ingestion Trigger Failed');
    return await response.json();
  },
  triggerAllIngestion: async (): Promise<{ message: string }> => {
    const response = await fetch(`${API_BASE}/admin/ingestion/run-all`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Run-All Ingestion Failed');
    return await response.json();
  },
};

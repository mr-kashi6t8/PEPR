export interface EconomicIndicator {
  id: string;
  name: string;
  code: string;
  category: string;
  unit: string;
  frequency: string;
  source: string;
  latest_value: number;
  previous_value: number;
  pct_change: number;
  last_updated: string;
  importance: 'HIGH' | 'MEDIUM' | 'LOW';
}

export type MacroIndicator = EconomicIndicator;

export interface NewsArticleItem {
  id: string;
  title: string;
  url: string;
  content?: string;
  published_at?: string;
  is_youtube?: boolean;
}

export type NewsSentimentArticle = NewsArticleItem;

export interface IndicatorObservation {
  id: string;
  indicator_id: string;
  observation_date: string;
  value: number;
  data_quality_score?: number;
}

export interface DetectedTrend {
  id: string;
  indicator_id: string;
  indicator_name: string;
  indicator_code: string;
  trend_direction: string;
  current_value: number;
  previous_value: number;
  pct_change: number;
  period: string;
  severity: string;
  detection_method: string;
  confidence_score: number;
  created_at?: string | null;
}

export type TrendAnalysis = DetectedTrend;

export interface DetectedAnomaly {
  id: string;
  indicator_id: string;
  indicator_name: string;
  observation_date: string;
  actual_value: number;
  expected_value: number;
  anomaly_score: number;
  algorithm_used: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
}

export type AnomalyEvent = DetectedAnomaly;

export interface PolicyGap {
  id: string;
  target_id: string;
  actual_id: string;
  gap_value: number;
  gap_percentage: number;
  gap_status: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL';
  engine_score: number;
  magnitude_score: number;
  persistence_score: number;
  analysis_notes?: string;
  created_at?: string;
  target?: {
    id: string;
    target_name: string;
    target_value: number;
    target_unit: string;
    target_period: string;
    target_source: string;
    responsible_institution?: string;
    source_citation?: string;
    higher_is_better: boolean;
    importance_weight: number;
  };
  actual?: {
    id: string;
    actual_value: number;
    actual_period: string;
    actual_source: string;
  };
}

export type PolicyTargetGap = PolicyGap;

export interface EmergingProblem {
  id: string;
  title: string;
  description: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  status: 'OPEN' | 'UNDER_REVIEW' | 'RESOLVED';
  priority_score: number;
  confidence_score: number;
  affected_indicators: string[];
  evidence_count: number;
  created_at: string;
}

export interface ProblemDetail extends EmergingProblem {
  executive_summary: string;
  evidence_timeline: Array<{
    date: string;
    event: string;
    type: 'ANOMALY' | 'NEWS' | 'POLICY' | 'RESEARCH';
  }>;
  related_indicators: EconomicIndicator[];
  related_news: Array<{
    id: string;
    title: string;
    url: string;
    published_at: string;
    sentiment_score: number;
    source: string;
  }>;
  related_policy_gaps: PolicyGap[];
  related_pide_research: Array<{
    id: string;
    title: string;
    authors: string;
    year: number;
    document_identifier: string;
    url: string;
  }>;
  ai_analysis: {
    root_cause: string;
    impact_assessment: string;
    recommended_interventions: string[];
    prompt_version: string;
    model: string;
  };
  data_provenance: Array<{
    source_name: string;
    reliability_tier: string;
    last_synced: string;
  }>;
}

export interface PIDEResearchDocument {
  id: string;
  title: string;
  authors: string;
  published_date: string;
  year: number;
  document_type: 'Working Paper' | 'Policy Brief' | 'Research Report' | 'Special Edition';
  document_identifier: string;
  original_url: string;
  abstract: string;
  topics: string[];
}

export type ResearchDoc = PIDEResearchDocument;

export interface GeneratedReport {
  id: string;
  title: string;
  status: 'COMPLETED' | 'GENERATING' | 'FAILED';
  report_date: string;
  version: number;
  pdf_path?: string;
  html_path?: string;
  created_at: string;
  structured_data?: {
    executive_summary: string;
    top_10_problems: Array<{
      problem_title: string;
      severity_level: string;
      root_cause_analysis: string;
      impact_assessment: string;
    }>;
    economic_indicator_trends: Array<{
      trend_name: string;
      direction: string;
      key_drivers: string[];
      historical_context?: string;
    }>;
    policy_gaps: Array<{
      policy_name: string;
      gap_reasoning: string;
      systemic_issues: string[];
    }>;
    emerging_news_topics: string[];
    relevant_pide_research: Array<{
      problem_statement: string;
      suggested_solution: string;
      key_interventions: string[];
      confidence_score: number;
    }>;
    evidence_and_citations: Array<{
      text: string;
      source_url?: string;
      research_paper_id?: string;
      indicator_id?: string;
    }>;
    methodology: string;
    data_quality_notes: string;
    model: string;
    prompt_version: string;
    timestamp: string;
  };
}

export interface DataSourceStatus {
  id: string;
  name: string;
  code: string;
  type: string;
  status: 'ONLINE' | 'DEGRADED' | 'OFFLINE' | 'RUNNING';
  last_run: string;
  records_ingested: number;
  error_rate: number;
  frequency: string;
}

export interface IngestionJob {
  id: string;
  source_name: string;
  status: 'SUCCESS' | 'RUNNING' | 'FAILED';
  started_at: string;
  completed_at?: string;
  records_processed: number;
  log_snippet?: string;
}

export interface SystemHealth {
  overall_status: 'HEALTHY' | 'WARNING' | 'CRITICAL';
  database_status: string;
  vector_db_status: string;
  ai_gateway_status: string;
  active_jobs: number;
  uptime_seconds: number;
}

export interface SystemAlert {
  id: string;
  title: string;
  message: string;
  details?: string;
  url?: string;
  content?: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO' | 'HIGH' | 'MEDIUM' | 'LOW';
  category: 'ANOMALY' | 'POLICY_GAP' | 'SYSTEM' | 'NEWS' | 'MEDIA_SENTIMENT' | 'MACRO_ANOMALY' | 'SYSTEM_INGESTION' | 'EMERGING_PROBLEM' | 'TALKSHOW_TRANSCRIPT';
  timestamp: string;
  is_read: boolean;
}

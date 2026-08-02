import React from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  BookOpen,
  FileText,
  Newspaper,
  ShieldCheck,
  TrendingUp,
  Brain,
  CheckCircle2,
  ExternalLink,
  Target,
} from 'lucide-react';
import { useProblemDetail } from '../api/hooks';
import { Card, CardHeader, CardTitle } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

export const ProblemDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { data: problem, isLoading } = useProblemDetail(id || 'prob-1');

  if (isLoading || !problem) {
    return <div className="p-8 text-center text-slate-500 font-medium">Loading Problem Intelligence Breakdown...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Back Link */}
      <Link to="/problems" className="inline-flex items-center gap-2 text-xs font-semibold text-[#005A36] hover:underline">
        <ArrowLeft className="w-3.5 h-3.5" />
        Back to Problems Radar
      </Link>

      {/* Title & Priority Header */}
      <div className="bg-[#0B2545] text-white p-6 rounded-2xl shadow-md border-l-8 border-[#D4AF37] flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Badge variant={problem.severity.toLowerCase() as any}>{problem.severity}</Badge>
            <span className="text-xs text-slate-300">• Status: {problem.status.toUpperCase()}</span>
          </div>
          <h1 className="text-2xl font-bold font-serif leading-tight">{problem.title}</h1>
          <p className="text-xs text-slate-300 max-w-3xl">{problem.description}</p>
        </div>

        <div className="flex flex-col items-center justify-center p-4 bg-[#071930] rounded-xl border border-slate-700 min-w-[150px]">
          <span className="text-[10px] text-[#D4AF37] font-bold uppercase tracking-wider">Priority Score</span>
          <span className="text-4xl font-extrabold font-mono text-[#D4AF37]">{problem.priority_score.toFixed(1)}</span>
          <span className="text-[10px] text-slate-400 mt-1">Confidence: {(problem.confidence_score * 100).toFixed(0)}%</span>
        </div>
      </div>

      {/* Grid: 2 Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main 2 Columns */}
        <div className="lg:col-span-2 space-y-6">
          {/* Executive Summary */}
          <Card>
            <CardHeader>
              <CardTitle>
                <FileText className="w-5 h-5 text-[#005A36]" />
                <span>Executive Problem Summary</span>
              </CardTitle>
            </CardHeader>
            <p className="text-xs text-slate-700 leading-relaxed font-medium">{problem.executive_summary}</p>
          </Card>

          {/* AI Root Cause & Intervention Synthesis */}
          <Card className="bg-gradient-to-br from-emerald-50/50 to-slate-50 border-emerald-200">
            <CardHeader>
              <CardTitle>
                <Brain className="w-5 h-5 text-[#005A36]" />
                <span>OpenRouter AI Synthesis & Recommended Interventions</span>
              </CardTitle>
              <span className="text-[10px] bg-[#005A36] text-white px-2 py-0.5 rounded font-mono">
                {problem.ai_analysis?.model || 'Gemini 2.5'} ({problem.ai_analysis?.prompt_version || 'v2.0.0-M5-RAG'})
              </span>
            </CardHeader>

            <div className="space-y-3 text-xs">
              <div>
                <h4 className="font-bold text-[#0B2545] uppercase text-[11px] tracking-wider">Root Cause Analysis:</h4>
                <p className="text-slate-700 mt-1">{problem.ai_analysis?.root_cause || problem.description}</p>
              </div>

              <div>
                <h4 className="font-bold text-[#0B2545] uppercase text-[11px] tracking-wider">Economic Impact Assessment:</h4>
                <p className="text-slate-700 mt-1">{problem.ai_analysis?.impact_assessment || 'Significant macroeconomic friction impacting growth and fiscal sustainability.'}</p>
              </div>

              <div>
                <h4 className="font-bold text-[#005A36] uppercase text-[11px] tracking-wider">Actionable PIDE Research Interventions:</h4>
                <ul className="mt-1.5 space-y-1.5">
                  {(problem.ai_analysis?.recommended_interventions || []).map((item, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-slate-700 bg-white/70 p-2 rounded border border-emerald-100">
                      <CheckCircle2 className="w-4 h-4 text-[#005A36] flex-shrink-0 mt-0.5" />
                      <span className="font-medium">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </Card>

          {/* Related Policy Target Gaps */}
          {(problem.related_policy_gaps || []).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>
                  <Target className="w-5 h-5 text-amber-600" />
                  <span>Statutory Policy Target Deviations</span>
                </CardTitle>
              </CardHeader>

              <div className="space-y-3">
                {problem.related_policy_gaps.map((gap: any, idx: number) => (
                  <div key={idx} className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between gap-4">
                    <div>
                      <span className="text-[10px] font-bold text-slate-400 font-mono">
                        {gap.target?.responsible_institution || 'Federal Policy'}
                      </span>
                      <h4 className="text-xs font-bold text-[#0B2545]">{gap.target?.target_name || 'Policy Target'}</h4>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        Target: <span className="font-semibold text-slate-700">{gap.target?.target_value} {gap.target?.target_unit}</span> | Actual: <span className="font-semibold text-slate-700">{gap.actual?.actual_value} {gap.target?.target_unit}</span>
                      </p>
                    </div>

                    <div className="text-right">
                      <Badge variant={gap.gap_percentage < 0 ? 'critical' : 'success'}>
                        {gap.gap_percentage > 0 ? `+${gap.gap_percentage}%` : `${gap.gap_percentage}%`}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Evidence Timeline */}
          <Card>
            <CardHeader>
              <CardTitle>
                <TrendingUp className="w-5 h-5 text-[#0B2545]" />
                <span>Evidence Timeline</span>
              </CardTitle>
            </CardHeader>

            <div className="relative pl-6 space-y-4 border-l-2 border-slate-200 ml-2">
              {(problem.evidence_timeline || []).map((ev, idx) => (
                <div key={idx} className="relative">
                  <span className="absolute -left-[31px] top-0.5 w-3 h-3 rounded-full bg-[#005A36] border-2 border-white" />
                  <span className="text-[10px] font-bold text-slate-400 font-mono">{ev.date}</span>
                  <p className="text-xs font-semibold text-[#0B2545] mt-0.5">{ev.event}</p>
                  <Badge size="sm" variant="neutral" className="mt-1">
                    {ev.type}
                  </Badge>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Right Column: Research & Data Provenance */}
        <div className="space-y-6">
          {/* Related PIDE Research */}
          <Card>
            <CardHeader>
              <CardTitle>
                <BookOpen className="w-5 h-5 text-[#005A36]" />
                <span>Related PIDE Research</span>
              </CardTitle>
            </CardHeader>

            <div className="space-y-3">
              {(problem.related_pide_research || []).length > 0 ? (
                problem.related_pide_research.map((paper) => (
                  <div key={paper.id} className="p-3 bg-slate-50 rounded-lg border border-slate-200/80">
                    <span className="text-[10px] font-bold text-[#D4AF37] font-mono">{paper.document_identifier}</span>
                    <h4 className="text-xs font-bold text-[#0B2545] mt-0.5">{paper.title}</h4>
                    <p className="text-[11px] text-slate-500 mt-1">{paper.authors} ({paper.year})</p>
                    <a
                      href={paper.url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-[11px] text-[#005A36] font-semibold mt-2 hover:underline"
                    >
                      Download PDF <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-400 p-2">PIDE Research Showcase matched papers loading...</p>
              )}
            </div>
          </Card>

          {/* Related News Coverage */}
          <Card>
            <CardHeader>
              <CardTitle>
                <Newspaper className="w-5 h-5 text-[#0B2545]" />
                <span>News Momentum</span>
              </CardTitle>
            </CardHeader>

            <div className="space-y-3">
              {(problem.related_news || []).length > 0 ? (
                problem.related_news.map((n) => (
                  <a
                    key={n.id}
                    href={n.url}
                    target="_blank"
                    rel="noreferrer"
                    className="block p-3 bg-slate-50 rounded-lg border border-slate-200/80 hover:bg-slate-100 transition-colors"
                  >
                    <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                      <span>{n.source}</span>
                      <span>Sentiment: {n.sentiment_score}</span>
                    </div>
                    <h4 className="text-xs font-bold text-[#0B2545] mt-1">{n.title}</h4>
                  </a>
                ))
              ) : (
                <p className="text-xs text-slate-400 p-2">No media articles flagged for this domain in past 7 days.</p>
              )}
            </div>
          </Card>

          {/* Data Provenance */}
          <Card>
            <CardHeader>
              <CardTitle>
                <ShieldCheck className="w-5 h-5 text-emerald-600" />
                <span>Data Provenance</span>
              </CardTitle>
            </CardHeader>

            <div className="space-y-2 text-xs">
              {(problem.data_provenance || []).map((prov, idx) => (
                <div key={idx} className="flex justify-between py-1 border-b border-slate-100 last:border-0">
                  <span className="font-semibold text-slate-700">{prov.source_name}</span>
                  <span className="text-[10px] text-slate-500 font-mono">{prov.reliability_tier}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

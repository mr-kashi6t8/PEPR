import React, { useMemo } from 'react';
import { GitCompare, Target, FileText, TrendingDown, TrendingUp, Minus } from 'lucide-react';
import { useGaps } from '../api/hooks';
import { Card, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { TargetVsActualChart } from '../components/charts/TargetVsActualChart';

export const GapsPage: React.FC = () => {
  const { data: gaps = [] } = useGaps();

  // Deduplicate: keep only the most recent gap per policy target (by target_name or target_id)
  const latestGaps = useMemo(() => {
    const seen = new Map<string, any>();
    // gaps are sorted desc by created_at from the API
    for (const gap of gaps) {
      const nameKey = (gap.target?.target_name || (gap as any).policy_name || gap.target_id || gap.id || '')
        .toString()
        .trim()
        .toLowerCase();
      if (nameKey && !seen.has(nameKey)) {
        seen.set(nameKey, gap);
      }
    }
    return Array.from(seen.values());
  }, [gaps]);

  const gapStatusIcon = (status: string) => {
    if (status === 'NEGATIVE') return <TrendingDown className="w-3.5 h-3.5 text-red-500" />;
    if (status === 'POSITIVE') return <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />;
    return <Minus className="w-3.5 h-3.5 text-slate-400" />;
  };

  const gapBadgeVariant = (status: string): 'critical' | 'success' | 'medium' => {
    if (status === 'NEGATIVE') return 'critical';
    if (status === 'POSITIVE') return 'success';
    return 'medium';
  };

  // Prepare data for Target vs Actual Chart
  const chartData = useMemo(() => {
    return latestGaps.map((gap) => {
      const target = gap.target;
      const actual = gap.actual;
      const name = target?.target_name || 'Policy Target';
      const targetVal = target?.target_value ?? gap.target_value ?? 0;
      const actualVal = actual?.actual_value ?? gap.actual_value ?? 0;
      const unit = target?.target_unit || '';
      const gapPct = typeof gap.gap_percentage === 'number' ? gap.gap_percentage : 0;
      const status = gap.gap_status || 'NEUTRAL';

      return {
        name,
        target: typeof targetVal === 'number' ? targetVal : parseFloat(targetVal) || 0,
        actual: typeof actualVal === 'number' ? actualVal : parseFloat(actualVal) || 0,
        unit,
        gapPct,
        status,
      };
    });
  }, [latestGaps]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold font-serif text-[#0B2545]">
          Policy Target vs. Actual Gap Analysis (M4)
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Quantitative tracking of statutory fiscal, monetary, and sectoral policy targets against actual empirical outputs.
          Auto-evaluated from live indicator data after every ingestion run.
        </p>
      </div>

      {/* Target vs Actual Comparison Chart */}
      <Card accentBorder>
        <CardHeader>
          <div>
            <CardTitle>
              <Target className="w-5 h-5 text-[#005A36]" />
              <span>Policy Target Deviation Radar</span>
            </CardTitle>
            <CardDescription>
              Comparing planned target bounds vs actual empirical observations across policy areas
            </CardDescription>
          </div>
        </CardHeader>
        <TargetVsActualChart data={chartData} />
      </Card>

      {/* Policy Gaps Table */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center w-full">
            <CardTitle>
              <GitCompare className="w-5 h-5 text-[#0B2545]" />
              <span>Active Policy Gaps Registry ({latestGaps.length} targets tracked)</span>
            </CardTitle>
            <span className="text-[10px] text-slate-400 italic">Latest ingestion run data · Auto-refreshed</span>
          </div>
        </CardHeader>

        {latestGaps.length === 0 ? (
          <div className="px-4 pb-4">
            <p className="text-xs text-slate-400 italic">
              No policy gaps found. Run the ingestion pipeline to auto-evaluate policy gaps against live indicator data.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50 text-[#0B2545] uppercase font-bold border-b border-slate-200">
                  <th className="py-3 px-4">Policy Target</th>
                  <th className="py-3 px-4">Period</th>
                  <th className="py-3 px-4">Target Value</th>
                  <th className="py-3 px-4">Actual Value</th>
                  <th className="py-3 px-4">Gap (%)</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Engine Score</th>
                  <th className="py-3 px-4">Institution</th>
                  <th className="py-3 px-4">Source</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {latestGaps.map((gap) => {
                  const target = gap.target;
                  const actual = gap.actual;
                  const policyName = target?.target_name || 'Policy Target';
                  const targetValue = target?.target_value ?? gap.target_value ?? '—';
                  const targetUnit = target?.target_unit || '';
                  const actualValue = actual?.actual_value ?? gap.actual_value ?? '—';
                  const period = target?.target_period || actual?.actual_period || '—';
                  const institution = target?.responsible_institution || '—';
                  const citation = target?.source_citation || target?.target_source || '—';
                  const gapPct = typeof gap.gap_percentage === 'number' ? gap.gap_percentage : 0;
                  const engineScore = typeof gap.engine_score === 'number' ? gap.engine_score : 0;
                  const status = gap.gap_status || 'NEUTRAL';

                  return (
                    <tr key={gap.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3.5 px-4 font-bold text-[#0B2545] max-w-[180px]">
                        <span className="truncate block">{policyName}</span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-500 font-mono text-[11px]">{period}</td>
                      <td className="py-3.5 px-4 font-mono">
                        {typeof targetValue === 'number' ? targetValue.toLocaleString() : targetValue}
                        {targetUnit && <span className="text-slate-400 ml-1 text-[10px]">{targetUnit}</span>}
                      </td>
                      <td className="py-3.5 px-4 font-mono font-bold text-[#0B2545]">
                        {typeof actualValue === 'number' ? actualValue.toLocaleString() : actualValue}
                        {targetUnit && <span className="text-slate-400 ml-1 text-[10px]">{targetUnit}</span>}
                      </td>
                      <td className="py-3.5 px-4">
                        <Badge variant={gapBadgeVariant(status)}>
                          {gapPct > 0 ? '+' : ''}{gapPct.toFixed(2)}%
                        </Badge>
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-1">
                          {gapStatusIcon(status)}
                          <span className={`text-[11px] font-bold ${
                            status === 'NEGATIVE' ? 'text-red-600' :
                            status === 'POSITIVE' ? 'text-emerald-600' : 'text-slate-500'
                          }`}>{status}</span>
                        </div>
                      </td>
                      <td className="py-3.5 px-4 font-mono font-bold text-[#005A36]">
                        {engineScore.toFixed(1)}
                      </td>
                      <td className="py-3.5 px-4 text-slate-600 text-[11px]">{institution}</td>
                      <td className="py-3.5 px-4 text-slate-500 italic">
                        <div className="flex items-center gap-1 max-w-[140px]">
                          <FileText className="w-3.5 h-3.5 text-[#D4AF37] flex-shrink-0" />
                          <span className="truncate">{citation}</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Sub-cards: Severity & Persistence breakdown */}
      {latestGaps.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {latestGaps.map((gap) => {
            const target = gap.target;
            const policyName = target?.target_name || 'Policy Target';
            const status = gap.gap_status || 'NEUTRAL';
            const magScore = typeof gap.magnitude_score === 'number' ? gap.magnitude_score : 0;
            const persScore = typeof gap.persistence_score === 'number' ? gap.persistence_score : 0;

            return (
              <Card key={gap.id} className="bg-slate-50/50">
                <div className="flex items-start justify-between gap-2">
                  <h4 className="text-sm font-bold text-[#0B2545] leading-tight">{policyName}</h4>
                  <Badge variant={gapBadgeVariant(status)} className="flex-shrink-0">{status}</Badge>
                </div>
                <div className="mt-3 space-y-2 text-xs">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500">Magnitude Score:</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-[#005A36] rounded-full"
                          style={{ width: `${Math.min(magScore * 10, 100)}%` }}
                        />
                      </div>
                      <span className="font-mono font-bold w-10 text-right">{magScore.toFixed(1)}/10</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500">Persistence Score:</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-amber-400 rounded-full"
                          style={{ width: `${Math.min(persScore * 20, 100)}%` }}
                        />
                      </div>
                      <span className="font-mono font-bold w-10 text-right">{persScore.toFixed(1)}/5</span>
                    </div>
                  </div>
                  {gap.analysis_notes && (
                    <p className="mt-2 text-slate-600 border-t border-slate-200 pt-2 italic text-[11px]">
                      "{gap.analysis_notes}"
                    </p>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};

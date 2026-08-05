import React from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  GitCompare,
  FileText,
  Activity,
  Zap,
} from 'lucide-react';
import {
  useIndicators,
  useGaps,
  useProblems,
  useReports,
} from '../api/hooks';
import { useAuth, type UserRole } from '../context/AuthContext';
import { api } from '../api/client';
import { Card, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { CardSkeleton } from '../components/ui/Skeleton';
import { TrendLineChart } from '../components/charts/TrendLineChart';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const currentRole: UserRole = user?.role || 'RESEARCHER';

  const { data: indicators = [], isLoading: loadingInd } = useIndicators();
  const { data: gaps = [] } = useGaps();
  const { data: problems = [] } = useProblems();
  const { data: reports = [] } = useReports();

  const [cpiChartData, setCpiChartData] = React.useState<any[]>([]);

  React.useEffect(() => {
    async function loadCpiChart() {
      if (indicators.length === 0) return;
      const cpiInd = indicators.find(
        (i) => i.code === 'PAK_CPI_YOY' || i.code.includes('CPI')
      );
      if (cpiInd) {
        try {
          const history = await api.getIndicatorHistory(cpiInd.code);
          const targetVal = 7.0;

          const points = history.map((h: any, idx: number) => ({
            date: h.date || (h.timestamp ? h.timestamp.substring(0, 7) : `P${idx + 1}`),
            value: Number(h.value),
            benchmark: Number(targetVal),
          }));
          setCpiChartData(points);
        } catch (err) {
          console.error('Failed to load CPI history for dashboard:', err);
        }
      }
    }
    loadCpiChart();
  }, [indicators]);

  const roleBanners: Record<UserRole, { title: string; subtitle: string; badge: string }> = {
    RESEARCHER: {
      badge: 'Policy Economist Workspace',
      title: 'Pakistan Economic Problem Radar — Research Portal',
      subtitle: 'Synthesis of empirical indicators, time-series anomaly detection, statutory gaps, and PIDE working paper RAG.',
    },
    MANAGEMENT: {
      badge: 'Executive Briefing Suite',
      title: 'PIDE Executive Decision Support System',
      subtitle: 'High-level executive briefing across macro indicators, weekly economic reports, and statutory policy target gaps.',
    },
    ICT: {
      badge: 'Data Operations Center',
      title: 'ICT Ingestion & Pipeline Monitoring Center',
      subtitle: 'Monitor real-time SBP, PBS, RSS, and YouTube data connectors, database sync status, and ingestion job logs.',
    },
    ADMIN: {
      badge: 'System Master Control',
      title: 'PEPR Master Administration & Provisioning Panel',
      subtitle: 'Unrestricted control over system health, RBAC user account provisioning, data ingestion pipelines, and AI engines.',
    },
  };

  return (
    <div className="space-y-6">
      {/* Institutional Top Header Tailored per Role */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#0B2545] text-white p-6 rounded-2xl shadow-md border-l-8 border-[#D4AF37]">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-[#D4AF37] text-[#0B2545] uppercase tracking-wider">
              {roleBanners[currentRole].badge}
            </span>
            <span className="text-xs text-slate-300">Role: {currentRole} | Real Database Active</span>
          </div>
          <h1 className="text-2xl font-extrabold font-serif tracking-tight mt-1">
            {roleBanners[currentRole].title}
          </h1>
          <p className="text-xs text-slate-300 mt-1 max-w-2xl">
            {roleBanners[currentRole].subtitle}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {(currentRole === 'MANAGEMENT' || currentRole === 'RESEARCHER' || currentRole === 'ADMIN') && (
            <Link to="/reports">
              <Button variant="gold" icon={<FileText className="w-4 h-4" />}>
                Latest Weekly Report
              </Button>
            </Link>
          )}
          {(currentRole === 'ICT' || currentRole === 'ADMIN') && (
            <Link to="/admin">
              <Button variant="gold" icon={<Zap className="w-4 h-4" />}>
                Data Pipelines Panel
              </Button>
            </Link>
          )}
        </div>
      </div>

      {/* Overview Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {loadingInd ? (
          <>
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
          </>
        ) : (
          <>
            <Card className="flex items-center gap-4">
              <div className="p-3 bg-emerald-50 rounded-xl text-[#005A36]">
                <Activity className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs text-slate-500 font-medium">Macro & Commodities</p>
                <h3 className="text-xl font-bold text-[#0B2545]">{indicators.length} Active</h3>
                <span className="text-[10px] text-emerald-600 font-semibold">SBP, PBS, OGRA & Commodities</span>
              </div>
            </Card>

            <Card className="flex items-center gap-4">
              <div className="p-3 bg-red-50 rounded-xl text-red-600">
                <GitCompare className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs text-slate-500 font-medium">Statutory Policy Gaps</p>
                <h3 className="text-xl font-bold text-[#0B2545]">{gaps.length} Target Gaps</h3>
                <span className="text-[10px] text-red-600 font-semibold">SBP, OGRA, FBR & MoE Gaps</span>
              </div>
            </Card>

            <Card className="flex items-center gap-4">
              <div className="p-3 bg-amber-50 rounded-xl text-amber-600">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs text-slate-500 font-medium">Emerging Problems</p>
                <h3 className="text-xl font-bold text-[#0B2545]">{problems.length} Synthesized</h3>
                <span className="text-[10px] text-amber-600 font-semibold">7-Day Database Evidence</span>
              </div>
            </Card>

            <Card className="flex items-center gap-4">
              <div className="p-3 bg-sky-50 rounded-xl text-[#0284c7]">
                <FileText className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs text-slate-500 font-medium">Weekly Reports</p>
                <h3 className="text-xl font-bold text-[#0B2545]">{reports.length} Reports</h3>
                <span className="text-[10px] text-[#0284c7] font-semibold">PIDE Executive Briefings</span>
              </div>
            </Card>
          </>
        )}
      </div>

      {/* CPI Inflation Chart vs Policy Target */}
      <Card accentBorder>
        <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <CardTitle>Inflation (CPI YoY %) vs SBP Medium-Term Target Band (7.0%)</CardTitle>
            <CardDescription>
              Time-series tracking of Pakistan Consumer Price Index inflation against SBP target benchmark.
            </CardDescription>
          </div>
          <Link to="/indicators">
            <Button size="sm" variant="outline">
              Inspect All {indicators.length} Indicators →
            </Button>
          </Link>
        </CardHeader>
        <div className="p-4 bg-slate-50 rounded-xl border border-slate-200/60">
          <TrendLineChart
            data={cpiChartData}
            name1="CPI Inflation YoY %"
            name2="SBP Target Benchmark (7.0%)"
            unit="%"
          />
        </div>
      </Card>

      {/* Two Column Grid: Critical Gaps & Emerging Problems */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Statutory Policy Target Gaps */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Statutory Policy Target Gaps</CardTitle>
              <CardDescription>Official government targets vs actual performance</CardDescription>
            </div>
            <Link to="/gaps" className="text-xs font-bold text-[#005A36] hover:underline">
              View All {gaps.length} Gaps →
            </Link>
          </CardHeader>
          <div className="space-y-3">
            {gaps.slice(0, 4).map((gap) => (
              <div
                key={gap.id}
                className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/80 flex items-center justify-between text-xs"
              >
                <div className="space-y-1">
                  <div className="font-bold text-[#0B2545]">{gap.target?.target_name || 'Policy Benchmark Target'}</div>
                  <div className="text-[11px] text-slate-500">
                    Target: <strong>{gap.target?.target_value} {gap.target?.target_unit}</strong> | Actual: <strong>{gap.actual?.actual_value} {gap.target?.target_unit}</strong>
                  </div>
                </div>
                <Badge variant={gap.gap_status === 'NEGATIVE' ? 'critical' : 'medium'}>
                  {gap.gap_status}
                </Badge>
              </div>
            ))}
          </div>
        </Card>

        {/* Top Emerging Economic Problems */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Emerging Economic Problems</CardTitle>
              <CardDescription>Synthesized from 7-day empirical database evidence</CardDescription>
            </div>
            <Link to="/problems" className="text-xs font-bold text-[#005A36] hover:underline">
              View All {problems.length} Problems →
            </Link>
          </CardHeader>
          <div className="space-y-3">
            {problems.slice(0, 4).map((prob) => (
              <div
                key={prob.id}
                className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/80 flex items-center justify-between text-xs"
              >
                <div className="space-y-1">
                  <div className="font-bold text-[#0B2545]">{prob.title}</div>
                  <div className="text-[11px] text-slate-500 line-clamp-1">{prob.description}</div>
                </div>
                <Badge variant={prob.severity === 'CRITICAL' ? 'critical' : 'high'}>
                  {prob.severity}
                </Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

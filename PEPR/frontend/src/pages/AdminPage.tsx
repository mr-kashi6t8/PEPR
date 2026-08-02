import React from 'react';
import { Shield, Database, RefreshCw, CheckCircle2, XCircle, Play, Activity, Zap, Lock } from 'lucide-react';
import { useAdminData, useTriggerAllIngestionMutation, useTriggerIngestionMutation } from '../api/hooks';
import { useAuth } from '../context/AuthContext';
import { Card, CardHeader, CardTitle } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';

export const AdminPage: React.FC = () => {
  const { sources, jobs, health, refetch } = useAdminData();
  const { canRunIngestion, user } = useAuth();

  const triggerIngestionMutation = useTriggerIngestionMutation();
  const triggerAllIngestionMutation = useTriggerAllIngestionMutation();

  const activeRunningSources = sources.filter((s) => s.status === 'RUNNING');
  const activeRunningJobs = jobs.filter((j) => j.status === 'RUNNING');
  const isIngestionActive =
    triggerAllIngestionMutation.isPending ||
    triggerIngestionMutation.isPending ||
    activeRunningSources.length > 0 ||
    activeRunningJobs.length > 0;

  const totalRecordsFetched = jobs.reduce((sum, j) => sum + (j.records_processed || 0), 0);
  const successJobsCount = jobs.filter((j) => j.status === 'SUCCESS').length;

  const statusIcon = (status: string) => {
    if (status === 'ONLINE' || status === 'SUCCESS') return <CheckCircle2 className="w-4 h-4 text-emerald-600" />;
    if (status === 'DEGRADED' || status === 'RUNNING') return <Activity className="w-4 h-4 text-amber-500 animate-spin" />;
    return <XCircle className="w-4 h-4 text-red-500" />;
  };

  const formatSourceType = (type: string) => {
    switch (type.toLowerCase()) {
      case 'sbp': return 'M1 SBP API';
      case 'pbs': return 'M1 PBS Scraper';
      case 'rss': return 'M1 News RSS Feed';
      case 'public_discussion': return 'M3 Public Discussion Bundle';
      case 'fbr': return 'M1 FBR Scraper';
      case 'psx': return 'M1 PSX API';
      case 'youtube': return 'M3 YouTube Transcripts';
      case 'worldbank': return 'M1 WorldBank Macro API';
      default: return `M1/M3 (${type})`;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold font-serif text-[#0B2545]">
              Data Pipeline Administration & System Health
            </h1>
            <Badge variant={canRunIngestion ? 'success' : 'medium'}>
              ACTIVE ROLE: {user?.role || 'GUEST'}
            </Badge>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Configure data source connectors (M1 & M3), monitor ingestion jobs, and inspect live pipeline health.
          </p>

          {!canRunIngestion && (
            <div className="mt-2 p-2.5 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800 flex items-center gap-2">
              <Lock className="w-4 h-4 text-amber-600 flex-shrink-0" />
              <span>Signed in as <strong>{user?.role}</strong>. Live ingestion pipeline execution is restricted to <strong>ICT</strong> and <strong>ADMIN</strong> roles.</span>
            </div>
          )}

          {triggerIngestionMutation.isError && (
            <p className="mt-2 text-sm text-red-600">Run Now failed: {(triggerIngestionMutation.error as Error)?.message || 'Unknown error'}</p>
          )}
          {triggerIngestionMutation.isSuccess && (
            <p className="mt-2 text-sm text-emerald-600">Ingestion job triggered! Live database metrics updated across all screens.</p>
          )}
          {triggerAllIngestionMutation.isError && (
            <p className="mt-2 text-sm text-red-600">Run All failed: {(triggerAllIngestionMutation.error as Error)?.message || 'Unknown error'}</p>
          )}
          {triggerAllIngestionMutation.isSuccess && (
            <p className="mt-2 text-sm text-emerald-600">Run All sweep completed successfully. All screens refreshed with live database data.</p>
          )}
        </div>

        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            icon={<RefreshCw className={`w-4 h-4 ${isIngestionActive ? 'animate-spin' : ''}`} />}
            onClick={() => refetch()}
            disabled={isIngestionActive}
          >
            {isIngestionActive ? 'Monitoring Pipeline...' : 'Refresh Status'}
          </Button>

          <Button
            variant="gold"
            icon={<Zap className="w-4 h-4" />}
            isLoading={triggerAllIngestionMutation.isPending}
            disabled={isIngestionActive || !canRunIngestion}
            title={!canRunIngestion ? 'Ingestion triggers restricted to ICT and ADMIN roles' : 'Trigger full ingestion across all sources'}
            onClick={() => triggerAllIngestionMutation.mutate()}
          >
            {triggerAllIngestionMutation.isPending ? 'Executing Run All...' : 'Run All Ingestion Pipelines'}
          </Button>
        </div>
      </div>

      {/* System Health Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="flex items-center gap-4">
          <div className="p-3 bg-emerald-50 rounded-xl text-emerald-700">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Database Node</p>
            <h3 className="text-lg font-bold text-[#0B2545]">{health?.database_status || 'HEALTHY'}</h3>
            <span className="text-[10px] text-emerald-600 font-semibold">SQLite Real DB Active</span>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="p-3 bg-sky-50 rounded-xl text-[#0369a1]">
            <Database className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Data Connectors</p>
            <h3 className="text-lg font-bold text-[#0B2545]">{sources.length} Active Sources</h3>
            <span className="text-[10px] text-slate-500">SBP, PBS, RSS, YouTube</span>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="p-3 bg-purple-50 rounded-xl text-purple-700">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Ingestion Pipeline</p>
            <h3 className="text-lg font-bold text-[#0B2545]">{successJobsCount} Jobs Completed</h3>
            <span className="text-[10px] text-purple-600 font-semibold">{totalRecordsFetched} Records Processed</span>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="p-3 bg-amber-50 rounded-xl text-amber-700">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Pipeline RBAC Permission</p>
            <h3 className="text-lg font-bold text-[#0B2545]">{canRunIngestion ? 'PERMITTED' : 'RESTRICTED'}</h3>
            <span className="text-[10px] text-slate-500">{canRunIngestion ? 'ICT / ADMIN Enabled' : 'Researcher / Management View'}</span>
          </div>
        </Card>
      </div>

      {/* Data Connectors List */}
      <Card accentBorder>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>M1 & M3 Live Data Source Connectors</CardTitle>
            <p className="text-xs text-slate-500 mt-0.5">
              Configured automated connectors streaming time-series data, statutory benchmarks, and media talkshows.
            </p>
          </div>
        </CardHeader>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-50 text-slate-700 font-bold border-y border-slate-200">
              <tr>
                <th className="p-3">Source Name</th>
                <th className="p-3">Connector Type</th>
                <th className="p-3">Ingestion Frequency</th>
                <th className="p-3">Records Synced</th>
                <th className="p-3">Status</th>
                <th className="p-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {sources.map((src) => {
                const isRunningThis =
                  triggerIngestionMutation.isPending && triggerIngestionMutation.variables === src.id;
                const isCurrentSourceActive = isRunningThis || src.status === 'RUNNING';

                return (
                  <tr key={src.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="p-3 font-bold text-[#0B2545]">{src.name}</td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded font-mono text-[11px]">
                        {formatSourceType(src.type)}
                      </span>
                    </td>
                    <td className="p-3 text-slate-600">{src.frequency || 'Daily at 08:00 AM'}</td>
                    <td className="p-3 font-semibold text-slate-800">{src.records_ingested}</td>
                    <td className="p-3">
                      <div className="flex items-center gap-1.5">
                        {statusIcon(src.status)}
                        <span className="font-semibold text-slate-700">{src.status}</span>
                      </div>
                    </td>
                    <td className="p-3 text-right">
                      <Button
                        size="sm"
                        variant="primary"
                        icon={
                          isCurrentSourceActive ? (
                            <Activity className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <Play className="w-3.5 h-3.5" />
                          )
                        }
                        isLoading={isCurrentSourceActive}
                        disabled={isIngestionActive || !canRunIngestion}
                        title={!canRunIngestion ? 'Only ICT and ADMIN roles can trigger ingestion' : 'Run ingestion pipeline for this source now'}
                        onClick={() => triggerIngestionMutation.mutate(src.id)}
                      >
                        {isCurrentSourceActive ? 'Running...' : 'Run Pipeline'}
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Ingestion Audit Trail */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Ingestion Job Runs</CardTitle>
        </CardHeader>
        <div className="space-y-3">
          {jobs.slice(0, 8).map((job) => (
            <div
              key={job.id}
              className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 flex items-center justify-between text-xs"
            >
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-[#0B2545]">{job.source_name}</span>
                  <Badge variant={job.status === 'SUCCESS' ? 'success' : job.status === 'FAILED' ? 'critical' : 'medium'}>
                    {job.status}
                  </Badge>
                </div>
                <div className="text-[11px] text-slate-500 font-mono">
                  Started: {job.started_at} | Processed: {job.records_processed} records
                </div>
                {job.log_snippet && <div className="text-[10px] text-slate-400 font-mono">{job.log_snippet}</div>}
              </div>

              {statusIcon(job.status)}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

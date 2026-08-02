import React, { useState } from 'react';
import { Download, Play, Trash2, RefreshCw } from 'lucide-react';
import { useReports, useGenerateReportMutation, useDeleteReportMutation } from '../api/hooks';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';

export const ReportsPage: React.FC = () => {
  const { data: reports = [], refetch, isLoading } = useReports();
  const generateMutation = useGenerateReportMutation();
  const deleteMutation = useDeleteReportMutation();
  
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const activeReport = reports.find((r) => r.id === (selectedReportId || reports[0]?.id)) || reports[0];

  const handleGenerate = () => {
    setStatusMessage('Generating new weekly report...');
    generateMutation.mutate(undefined, {
      onSuccess: (data) => {
        setStatusMessage(data.message || 'Report generation triggered successfully.');
        setTimeout(() => {
          refetch();
          setStatusMessage(null);
        }, 3000);
      },
      onError: (err) => {
        setStatusMessage(`Report Generation Failed: ${err.message}`);
      }
    });
  };

  const handleDelete = (id: string, title: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (window.confirm(`Are you sure you want to delete report:\n"${title}"?`)) {
      setDeletingId(id);
      deleteMutation.mutate(id, {
        onSuccess: () => {
          setDeletingId(null);
          setStatusMessage('Report deleted successfully.');
          if (selectedReportId === id) {
            setSelectedReportId(null);
          }
          refetch();
          setTimeout(() => setStatusMessage(null), 3000);
        },
        onError: (err) => {
          setDeletingId(null);
          alert(`Failed to delete report: ${err.message}`);
        }
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with Official PIDE Branding */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-4">
          <img 
            src="/pide-logo.png" 
            alt="PIDE Logo" 
            className="h-14 w-auto object-contain"
            onError={(e) => {
              (e.target as HTMLElement).style.display = 'none';
            }}
          />
          <div>
            <div className="text-[11px] font-bold text-[#0284c7] uppercase tracking-wider">
              Pakistan Institute of Development Economics (PIDE)
            </div>
            <h1 className="text-2xl font-extrabold font-serif text-[#0B2545]">
              Weekly Executive Economic Radar Reports
            </h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Automated weekly policy synthesis generated from live PEPR evidence (M1-M5) with cited PIDE Research Showcase recommendations.
            </p>
          </div>
        </div>

        <Button
          variant="gold"
          icon={<Play className="w-4 h-4" />}
          isLoading={generateMutation.isPending}
          onClick={handleGenerate}
        >
          Trigger Manual Synthesis Run
        </Button>
      </div>

      {/* Notification Toast */}
      {statusMessage && (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs font-semibold text-blue-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
            <span>{statusMessage}</span>
          </div>
          <button onClick={() => setStatusMessage(null)} className="text-blue-500 hover:text-blue-700">✕</button>
        </div>
      )}

      {/* Grid: Left List, Right Detailed Report View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Report List */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Report Archives ({reports.length})</h3>
            {isLoading && <span className="text-xs text-slate-400">Refreshing...</span>}
          </div>

          {reports.length === 0 ? (
            <Card>
              <div className="p-6 text-center text-xs text-slate-500">
                No reports generated yet. Click "Trigger Manual Synthesis Run" above to generate your first executive report.
              </div>
            </Card>
          ) : (
            reports.map((rep) => {
              const isSelected = activeReport?.id === rep.id;
              const isDeleting = deletingId === rep.id;

              return (
                <Card
                  key={rep.id}
                  hoverable
                  onClick={() => setSelectedReportId(rep.id)}
                  className={`cursor-pointer transition-all relative group ${
                    isSelected ? 'border-[#005A36] ring-2 ring-[#005A36]/20 bg-emerald-50/20' : ''
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <span className="text-[10px] font-bold text-slate-400 font-mono">{rep.report_date}</span>
                    <div className="flex items-center gap-2">
                      <Badge variant={rep.status === 'COMPLETED' ? 'success' : rep.status === 'FAILED' ? 'critical' : 'medium'}>
                        {rep.status}
                      </Badge>
                      <button
                        onClick={(e) => handleDelete(rep.id, rep.title, e)}
                        disabled={isDeleting}
                        title="Delete Report"
                        className="p-1 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors opacity-80 group-hover:opacity-100"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  <h4 className="text-sm font-bold text-[#0B2545] mt-1 font-serif line-clamp-2">{rep.title}</h4>
                  
                  <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500">
                    <span>Version v{rep.version || 1}.0</span>
                    <span className="text-[#005A36] font-semibold flex items-center gap-1">
                      Inspect Report →
                    </span>
                  </div>
                </Card>
              );
            })
          )}
        </div>

        {/* Right Column: Interactive Executive Report Inspector */}
        <div className="lg:col-span-2 space-y-6">
          {activeReport ? (
            <Card accentBorder className="space-y-6">
              {/* Header inside Report Inspector */}
              <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-100 pb-4 gap-4">
                <div className="flex items-start gap-3">
                  <img 
                    src="/pide-logo.png" 
                    alt="PIDE" 
                    className="h-10 w-auto object-contain mt-1"
                    onError={(e) => (e.target as HTMLElement).style.display = 'none'} 
                  />
                  <div>
                    <div className="flex items-center gap-2">
                      <Badge variant={activeReport.status === 'COMPLETED' ? 'success' : 'medium'}>
                        STATUS: {activeReport.status}
                      </Badge>
                      <span className="text-xs text-slate-400 font-mono">Date: {activeReport.report_date}</span>
                      <span className="text-xs text-slate-400 font-mono">Version: v{activeReport.version || 1}.0</span>
                    </div>
                    <h2 className="text-xl font-bold font-serif text-[#0B2545] mt-1">{activeReport.title}</h2>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <a href={`/api/v1/reports/${activeReport.id}/pdf`} download>
                    <Button variant="primary" icon={<Download className="w-4 h-4" />}>
                      Download PDF
                    </Button>
                  </a>
                  <Button 
                    variant="outline"
                    icon={<Trash2 className="w-4 h-4 text-red-600" />}
                    onClick={(e) => handleDelete(activeReport.id, activeReport.title, e)}
                  >
                    Delete
                  </Button>
                </div>
              </div>

              {activeReport.structured_data ? (
                <>
                  {/* 1. Executive Summary */}
                  <div>
                    <h3 className="text-xs font-bold text-[#0B2545] uppercase tracking-wider border-b border-slate-100 pb-1 mb-2">
                      1. Executive Macroeconomic Summary
                    </h3>
                    <div className="p-4 bg-slate-50 border-l-4 border-[#D4AF37] rounded-r-lg text-xs text-slate-700 leading-relaxed font-sans">
                      {activeReport.structured_data.executive_summary}
                    </div>
                  </div>

                  {/* 2. Top Emerging Problems */}
                  {activeReport.structured_data.top_10_problems && (
                    <div>
                      <h3 className="text-xs font-bold text-[#0B2545] uppercase tracking-wider border-b border-slate-100 pb-1 mb-2">
                        2. Top Emerging Economic Problems
                      </h3>
                      <div className="space-y-3">
                        {activeReport.structured_data.top_10_problems.map((prob, idx) => (
                          <div key={idx} className="p-3 bg-white rounded-lg border border-slate-200 text-xs shadow-2xs">
                            <div className="flex justify-between items-center font-bold text-[#0B2545]">
                              <span className="font-serif">RANK #{idx + 1}: {prob.problem_title}</span>
                              <Badge variant={prob.severity_level === 'CRITICAL' ? 'critical' : prob.severity_level === 'HIGH' ? 'high' : 'medium'}>
                                {prob.severity_level}
                              </Badge>
                            </div>
                            <p className="mt-1 text-slate-600"><strong>Root Cause:</strong> {prob.root_cause_analysis}</p>
                            <p className="mt-0.5 text-slate-600"><strong>Impact:</strong> {prob.impact_assessment}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 3. Statutory Policy Target Deviations */}
                  {activeReport.structured_data.policy_gaps && activeReport.structured_data.policy_gaps.length > 0 && (
                    <div>
                      <h3 className="text-xs font-bold text-[#0B2545] uppercase tracking-wider border-b border-slate-100 pb-1 mb-2">
                        3. Statutory Policy Target Deviations (M4 Engine)
                      </h3>
                      <div className="overflow-x-auto">
                        <table className="w-full text-xs text-left border border-slate-200">
                          <thead className="bg-[#0B2545] text-white">
                            <tr>
                              <th className="p-2 border border-[#0B2545]">Policy Target Benchmark</th>
                              <th className="p-2 border border-[#0B2545]">Gap Assessment & Reasoning</th>
                              <th className="p-2 border border-[#0B2545]">Systemic Impact Factors</th>
                            </tr>
                          </thead>
                          <tbody>
                            {activeReport.structured_data.policy_gaps.map((gap, idx) => (
                              <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-slate-50'}>
                                <td className="p-2 font-bold border border-slate-200">{gap.policy_name}</td>
                                <td className="p-2 border border-slate-200">{gap.gap_reasoning}</td>
                                <td className="p-2 border border-slate-200">{gap.systemic_issues.join(', ')}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* 4. Relevant PIDE Research Showcase Interventions */}
                  {activeReport.structured_data.relevant_pide_research && activeReport.structured_data.relevant_pide_research.length > 0 && (
                    <div>
                      <h3 className="text-xs font-bold text-[#0B2545] uppercase tracking-wider border-b border-slate-100 pb-1 mb-2">
                        4. Actionable Interventions from PIDE Research Showcase (M5 RAG)
                      </h3>
                      <div className="space-y-3">
                        {activeReport.structured_data.relevant_pide_research.map((rec, idx) => (
                          <div key={idx} className="p-3 bg-sky-50/50 border-l-4 border-[#0284c7] rounded-r-lg text-xs space-y-1">
                            <div className="font-bold text-[#0369a1] font-serif">Macro Target: {rec.problem_statement}</div>
                            <p className="text-slate-700"><strong>PIDE Policy Intervention:</strong> {rec.suggested_solution}</p>
                            {rec.key_interventions && (
                              <ul className="list-disc list-inside text-slate-600 font-mono text-[11px] pl-1">
                                {rec.key_interventions.map((int, i) => (
                                  <li key={i}>{int}</li>
                                ))}
                              </ul>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 5. Methodology & Data Quality */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                    <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs">
                      <h4 className="font-bold text-[#0B2545]">System Methodology:</h4>
                      <p className="text-slate-600 mt-1">{activeReport.structured_data.methodology}</p>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs">
                      <h4 className="font-bold text-[#0B2545]">Data Quality & Audit Notes:</h4>
                      <p className="text-slate-600 mt-1">{activeReport.structured_data.data_quality_notes}</p>
                    </div>
                  </div>

                  {/* Metadata Footer */}
                  <div className="pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between text-[11px] text-slate-400 font-mono">
                    <span>Engine: {activeReport.structured_data.model}</span>
                    <span>Prompt Ver: {activeReport.structured_data.prompt_version}</span>
                    <span>Generated: {activeReport.structured_data.timestamp}</span>
                  </div>
                </>
              ) : (
                <div className="p-6 text-center text-xs text-slate-500">
                  This report is currently generating. Please wait a moment and click refresh.
                </div>
              )}
            </Card>
          ) : (
            <Card>
              <div className="p-8 text-center text-slate-500">Select a report from the archive to inspect details.</div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

import React, { useState } from 'react';
import { ShieldAlert, X, ExternalLink, Info, AlertTriangle } from 'lucide-react';
import { useAlerts } from '../api/hooks';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import type { SystemAlert } from '../api/types';

export const AlertsPage: React.FC = () => {
  const { data: alerts = [] } = useAlerts();
  const [selectedAlert, setSelectedAlert] = useState<SystemAlert | null>(null);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold font-serif text-[#0B2545]">
          Real-Time Anomaly & Media Sentiment Alerts
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Live automated alerts generated from PostgreSQL statistical anomalies, media sentiment shocks, and indicator shifts. Click any alert to view full evidence details.
        </p>
      </div>

      {/* Alerts Feed */}
      <div className="space-y-3">
        {alerts.map((alt) => (
          <Card
            key={alt.id}
            hoverable
            onClick={() => setSelectedAlert(alt)}
            className={`cursor-pointer transition-all ${
              !alt.is_read ? 'border-l-4 border-l-[#005A36] bg-emerald-50/10' : ''
            }`}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-red-50 text-red-600 mt-0.5 flex-shrink-0">
                  <ShieldAlert className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant={alt.severity.toLowerCase() as any}>{alt.severity}</Badge>
                    <span className="text-[11px] font-bold text-slate-400 font-mono">{alt.category}</span>
                    <span className="text-[11px] text-slate-400">• {alt.timestamp}</span>
                  </div>
                  <h3 className="text-sm font-bold text-[#0B2545] mt-1 font-serif hover:text-[#005A36] transition-colors">
                    {alt.title}
                  </h3>
                  <p className="text-xs text-slate-600 mt-0.5 line-clamp-2">{alt.message}</p>
                </div>
              </div>

              <div className="flex flex-col items-end gap-2 flex-shrink-0">
                {!alt.is_read && (
                  <span className="px-2 py-0.5 text-[10px] font-bold bg-[#D4AF37] text-[#0B2545] rounded-full uppercase tracking-wider">
                    New
                  </span>
                )}
                <span className="text-[11px] text-[#005A36] font-semibold hover:underline flex items-center gap-1">
                  View Details &rarr;
                </span>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Alert Detail Modal */}
      {selectedAlert && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 animate-fade-in">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full p-6 space-y-5 border border-slate-100 relative max-h-[90vh] overflow-y-auto">
            {/* Close Button */}
            <button
              onClick={() => setSelectedAlert(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 transition-colors p-1 rounded-full hover:bg-slate-100"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Header */}
            <div>
              <div className="flex items-center gap-2">
                <Badge variant={selectedAlert.severity.toLowerCase() as any}>{selectedAlert.severity}</Badge>
                <span className="text-xs font-mono font-bold text-slate-500">{selectedAlert.category}</span>
                <span className="text-xs text-slate-400">• {selectedAlert.timestamp}</span>
              </div>
              <h2 className="text-xl font-bold font-serif text-[#0B2545] mt-2">
                {selectedAlert.title}
              </h2>
            </div>

            {/* Main Message & Details */}
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200/80 space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold text-[#0B2545]">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <span>Detection Summary</span>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed font-medium">
                {selectedAlert.message}
              </p>
              {selectedAlert.details && (
                <p className="text-xs text-slate-600 pt-2 border-t border-slate-200 leading-relaxed">
                  {selectedAlert.details}
                </p>
              )}
            </div>

            {/* Article/Transcript Excerpt from DB */}
            {selectedAlert.content && (
              <div className="space-y-1.5">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                  <Info className="w-3.5 h-3.5 text-[#005A36]" />
                  <span>Real Database Evidence Excerpt</span>
                </h4>
                <div className="p-3 bg-white rounded-lg border border-slate-200 text-xs font-mono text-slate-700 leading-relaxed max-h-48 overflow-y-auto">
                  {selectedAlert.content}
                </div>
              </div>
            )}

            {/* Footer Action */}
            <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
              <Button variant="outline" size="sm" onClick={() => setSelectedAlert(null)}>
                Close
              </Button>

              {selectedAlert.url && (
                <a href={selectedAlert.url} target="_blank" rel="noreferrer">
                  <Button variant="primary" size="sm" icon={<ExternalLink className="w-3.5 h-3.5" />}>
                    Open Source Evidence
                  </Button>
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

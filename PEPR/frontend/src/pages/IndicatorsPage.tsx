import React from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { useIndicators } from '../api/hooks';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

export const IndicatorsPage: React.FC = () => {
  const { data: indicators = [] } = useIndicators();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold font-serif text-[#0B2545]">
          Macroeconomic Indicators Directory (M1)
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Catalog of macroeconomic indicators ingested from PBS, SBP, PSX, and World Bank APIs.
        </p>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {indicators.map((ind: any) => {
          const pctChange = typeof ind.pct_change === 'number' && !isNaN(ind.pct_change) 
            ? ind.pct_change 
            : (ind.trend?.pct_change || 0);
          const latestVal = typeof ind.latest_value === 'number' 
            ? ind.latest_value 
            : (ind.trend?.current_value ?? '--');
          const unit = ind.unit || '%';
          const isUp = pctChange > 0;

          const getBadgeVariant = (imp: string) => {
            const upper = (imp || '').toUpperCase();
            if (upper === 'CRITICAL') return 'critical';
            if (upper === 'HIGH') return 'high';
            if (upper === 'MEDIUM') return 'medium';
            return 'low';
          };

          return (
            <Card key={ind.id} hoverable accentBorder>
              <div className="flex justify-between items-start">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{ind.category || 'Macroeconomic'}</span>
                <Badge variant={getBadgeVariant(ind.importance)}>{ind.importance || 'MEDIUM'}</Badge>
              </div>

              <h3 className="text-lg font-bold text-[#0B2545] mt-1 font-serif">{ind.name}</h3>
              <p className="text-[11px] font-mono text-slate-400">Code: {ind.code}</p>

              <div className="mt-4 p-3 bg-slate-50 rounded-lg border border-slate-100 flex justify-between items-center">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase">Latest Observation</span>
                  <p className="text-2xl font-extrabold font-mono text-[#0B2545]">
                    {typeof latestVal === 'number' ? latestVal.toLocaleString('en-US', { maximumFractionDigits: 2 }) : latestVal} <span className="text-xs font-normal text-slate-500">{unit}</span>
                  </p>
                </div>

                <div className={`flex items-center font-bold text-sm ${isUp ? 'text-red-600' : 'text-emerald-600'}`}>
                  {isUp ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                  {Math.abs(pctChange).toFixed(1)}%
                </div>
              </div>

              {ind.policy_gap && (
                <div className="mt-2.5 p-2 bg-amber-50/80 rounded border border-amber-200/80 flex items-center justify-between text-[11px] text-amber-900 font-medium">
                  <span>Policy Target: {ind.policy_gap.target_value} {ind.policy_gap.target_unit}</span>
                  <span className="font-bold text-amber-700">Gap: {ind.policy_gap.gap_percentage > 0 ? '+' : ''}{Number(ind.policy_gap.gap_percentage).toFixed(1)}%</span>
                </div>
              )}

              <div className="mt-3 pt-2 border-t border-slate-100 flex justify-between items-center text-[11px] text-slate-500">
                <span className="truncate max-w-[180px]">Source: {ind.source || 'Official Database'}</span>
                <span>Freq: {ind.frequency || 'Monthly'}</span>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
};

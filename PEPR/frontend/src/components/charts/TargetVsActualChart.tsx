import React, { useState } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  Cell,
  LabelList,
} from 'recharts';
import { SlidersHorizontal, Percent, BarChart3, AlertCircle, Layers } from 'lucide-react';

export interface TargetVsActualDataItem {
  name: string;
  target: number;
  actual: number;
  unit?: string;
  gapPct?: number;
  status?: string;
}

interface TargetVsActualChartProps {
  data?: TargetVsActualDataItem[];
}

type ChartMode = 'achieved' | 'gap' | 'raw';

// Helper to normalize raw units (e.g. 2 Trillion PKR vs 12.97 Trillion target)
const normalizeScale = (actual: number, target: number) => {
  let a = actual;
  let t = target;

  if (Math.abs(a) > 1e8 && Math.abs(t) < 1000) {
    if (Math.abs(a) > 1e11) a = a / 1e12;
    else if (Math.abs(a) > 1e8) a = a / 1e9;
    else if (Math.abs(a) > 1e5) a = a / 1e6;
  }

  return { normActual: a, normTarget: t };
};

// Formatter for clean callout labels on top of bars (max 2 decimals, k/M/B/T suffixes)
const formatCalloutVal = (val: number | null | undefined): string => {
  if (val == null || isNaN(val)) return '';
  const abs = Math.abs(val);

  if (abs >= 1e12) return `${(val / 1e12).toFixed(2)}T`;
  if (abs >= 1e9) return `${(val / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${(val / 1e6).toFixed(2)}M`;
  if (abs >= 1000) return `${(val / 1000).toFixed(1)}k`;
  if (abs < 0.01 && abs > 0) return val.toFixed(3);
  return val % 1 === 0 ? val.toString() : val.toFixed(2);
};

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload || !payload.length) return null;
  const itemData: any = payload[0]?.payload;
  if (!itemData) return null;

  const unitStr = itemData.unit ? ` ${itemData.unit}` : '';
  const targetVal = itemData.rawTarget ?? itemData.target;
  const actualVal = itemData.rawActual ?? itemData.actual;
  const gapPct = itemData.gapPct;
  const targetAchieved = targetVal !== 0 ? ((actualVal / targetVal) * 100) : 100;

  return (
    <div className="bg-[#0B2545] text-white p-3.5 rounded-lg border border-[#D4AF37] shadow-xl text-xs space-y-1.5 max-w-xs">
      <p className="font-bold border-b border-slate-700/80 pb-1.5 text-slate-100 text-sm">
        {itemData.name}
      </p>
      
      <div className="flex justify-between items-center gap-4 text-slate-300">
        <span className="text-slate-400">Target Value:</span>
        <span className="font-mono font-semibold text-emerald-400">
          {typeof targetVal === 'number' ? formatCalloutVal(targetVal) : targetVal}{unitStr}
        </span>
      </div>

      <div className="flex justify-between items-center gap-4 text-slate-300">
        <span className="text-slate-400">Actual Output:</span>
        <span className="font-mono font-semibold text-amber-400">
          {typeof actualVal === 'number' ? formatCalloutVal(actualVal) : actualVal}{unitStr}
        </span>
      </div>

      <div className="flex justify-between items-center gap-4 text-slate-300 border-t border-slate-700/60 pt-1">
        <span className="text-slate-400">Target Achieved:</span>
        <span className="font-mono font-bold text-sky-300">
          {targetAchieved.toFixed(1)}%
        </span>
      </div>

      {typeof gapPct === 'number' && (
        <div className="flex justify-between items-center gap-4 border-t border-slate-700/60 pt-1">
          <span className="text-slate-400">Deviation Gap:</span>
          <span className={`font-mono font-bold ${gapPct < 0 ? 'text-red-400' : 'text-emerald-400'}`}>
            {gapPct > 0 ? '+' : ''}{gapPct.toFixed(2)}%
          </span>
        </div>
      )}
    </div>
  );
};

export const TargetVsActualChart: React.FC<TargetVsActualChartProps> = ({
  data = [],
}) => {
  const [mode, setMode] = useState<ChartMode>('achieved');
  const [useLogRaw, setUseLogRaw] = useState<boolean>(true); // Log scale for Raw mode so all indicators are visible

  if (!data || data.length === 0) {
    return (
      <div className="w-full h-64 flex items-center justify-center bg-slate-50/50 rounded-lg border border-dashed border-slate-200">
        <p className="text-xs text-slate-400 italic">No policy gap data available for radar comparison chart.</p>
      </div>
    );
  }

  // Transform data based on selected view mode with scale normalization and callout formatting
  const formattedData = data.map((d) => {
    const { normActual, normTarget } = normalizeScale(d.actual, d.target);

    // Calculate normalized % achieved
    const achievedPct = normTarget !== 0 ? (normActual / normTarget) * 100 : 100;

    // Calculate gap %
    const computedGap = typeof d.gapPct === 'number' && Math.abs(d.gapPct) < 5000
      ? d.gapPct
      : (normTarget !== 0 ? ((normActual - normTarget) / normTarget) * 100 : 0);

    if (mode === 'achieved') {
      return {
        ...d,
        rawTarget: normTarget,
        rawActual: normActual,
        gapPct: computedGap,
        displayTarget: 100,
        displayActual: Math.min(Math.max(Number(achievedPct.toFixed(1)), -50), 250),
        rawAchieved: Number(achievedPct.toFixed(1)),
      };
    } else if (mode === 'gap') {
      return {
        ...d,
        rawTarget: normTarget,
        rawActual: normActual,
        gapPct: computedGap,
        displayGap: Math.min(Math.max(Number(computedGap.toFixed(2)), -150), 250),
        rawGap: Number(computedGap.toFixed(2)),
      };
    } else {
      // Raw Values mode — apply log height scaling if enabled so small bars (GDP 3.6%) are clearly visible alongside PSX (85k)
      let displayTarget = normTarget;
      let displayActual = normActual;

      if (useLogRaw) {
        displayTarget = Math.sign(normTarget) * Math.log10(Math.abs(normTarget) + 1);
        displayActual = Math.sign(normActual) * Math.log10(Math.abs(normActual) + 1);
      }

      return {
        ...d,
        rawTarget: normTarget,
        rawActual: normActual,
        gapPct: computedGap,
        displayTarget: Number(displayTarget.toFixed(3)),
        displayActual: Number(displayActual.toFixed(3)),
      };
    }
  });

  // Calculate dynamic container width for all targets
  const minWidthPx = Math.max(data.length * 90, 650);

  // Define locked Y-axis domains
  const yAxisProps = mode === 'achieved'
    ? { domain: [0, 250], ticks: [0, 50, 100, 150, 200, 250] }
    : mode === 'gap'
    ? { domain: [-150, 250], ticks: [-150, -100, -50, 0, 50, 100, 150, 200, 250] }
    : useLogRaw
    ? { domain: [0, 5.5], ticks: [0, 1, 2, 3, 4, 5] }
    : { domain: ['auto' as const, 'auto' as const] };

  return (
    <div className="space-y-3">
      {/* Chart View Mode Controls */}
      <div className="flex flex-wrap items-center justify-between gap-2 bg-slate-50 p-2 rounded-lg border border-slate-200/80">
        <div className="flex items-center gap-1.5 text-xs text-slate-600 font-medium">
          <SlidersHorizontal className="w-3.5 h-3.5 text-[#005A36]" />
          <span>Radar View Mode ({data.length} Targets Tracked):</span>
        </div>

        <div className="flex items-center gap-1 flex-wrap">
          <button
            onClick={() => setMode('achieved')}
            className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all flex items-center gap-1 ${
              mode === 'achieved'
                ? 'bg-[#005A36] text-white shadow-sm'
                : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
            }`}
            title="Normalizes target baseline to 100% so all metric scales (%, PKR, Points) are directly comparable"
          >
            <Percent className="w-3 h-3" />
            <span>% Target Achieved (Normalized)</span>
          </button>

          <button
            onClick={() => setMode('gap')}
            className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all flex items-center gap-1 ${
              mode === 'gap'
                ? 'bg-[#005A36] text-white shadow-sm'
                : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
            }`}
            title="Plots deviation gap percentage (+ / -) across all policy targets"
          >
            <BarChart3 className="w-3 h-3" />
            <span>Deviation Gap (%)</span>
          </button>

          <button
            onClick={() => setMode('raw')}
            className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all ${
              mode === 'raw'
                ? 'bg-[#005A36] text-white shadow-sm'
                : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
            }`}
            title="Displays raw numerical values"
          >
            <span>Raw Values</span>
          </button>
        </div>
      </div>

      {mode === 'raw' && (
        <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-amber-800 bg-amber-50 px-3 py-1.5 rounded border border-amber-200/80">
          <div className="flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 text-amber-600" />
            <span>
              Raw values display formatted callout numbers on top of each bar.
            </span>
          </div>

          <button
            onClick={() => setUseLogRaw(!useLogRaw)}
            className="flex items-center gap-1 text-[11px] font-bold text-[#005A36] underline hover:text-[#0B2545]"
          >
            <Layers className="w-3 h-3" />
            <span>{useLogRaw ? 'Visual Log Scaling: ON (Click for Linear)' : 'Visual Log Scaling: OFF (Click for Log)'}</span>
          </button>
        </div>
      )}

      {/* Recharts Bar Container with Horizontal Scroll */}
      <div className="w-full h-84 pt-1 overflow-x-auto">
        <div style={{ width: `${minWidthPx}px`, minWidth: '100%', height: '100%' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={formattedData} margin={{ top: 25, right: 35, left: 15, bottom: 75 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 10, fill: '#0B2545', fontWeight: 600 }}
                interval={0}
                angle={-25}
                textAnchor="end"
                height={80}
              />
              <YAxis
                {...yAxisProps}
                tick={{ fontSize: 11, fill: '#64748B' }}
                tickFormatter={(val) => {
                  if (mode === 'achieved' || mode === 'gap') return `${val}%`;
                  if (mode === 'raw' && useLogRaw) {
                    const logVals: Record<number, string> = { 0: '0', 1: '10', 2: '100', 3: '1k', 4: '10k', 5: '100k' };
                    return logVals[val] || `${val}`;
                  }
                  if (Math.abs(val) >= 1e12) return `${(val / 1e12).toFixed(1)}T`;
                  if (Math.abs(val) >= 1e9) return `${(val / 1e9).toFixed(1)}B`;
                  if (Math.abs(val) >= 1e6) return `${(val / 1e6).toFixed(1)}M`;
                  if (Math.abs(val) >= 1000) return `${(val / 1000).toFixed(0)}k`;
                  return `${val}`;
                }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                verticalAlign="top"
                align="right"
                wrapperStyle={{ fontSize: '11px', paddingBottom: '8px' }}
              />

              {mode === 'achieved' && (
                <>
                  <ReferenceLine y={100} stroke="#005A36" strokeDasharray="4 4" label={{ value: 'Target Baseline (100%)', fill: '#005A36', fontSize: 10, position: 'insideTopLeft' }} />
                  <Bar dataKey="displayTarget" name="Policy Target (100%)" fill="#005A36" radius={[4, 4, 0, 0]} maxBarSize={32} />
                  <Bar dataKey="displayActual" name="Actual Performance (% of Target)" fill="#D4AF37" radius={[4, 4, 0, 0]} maxBarSize={32}>
                    <LabelList
                      dataKey="rawAchieved"
                      position="top"
                      formatter={(val: any) => (val != null ? `${val}%` : '')}
                      style={{ fontSize: '9px', fontWeight: 700, fill: '#0B2545' }}
                    />
                  </Bar>
                </>
              )}

              {mode === 'gap' && (
                <>
                  <ReferenceLine y={0} stroke="#64748B" strokeWidth={1.5} />
                  <Bar dataKey="displayGap" name="Deviation Gap (%)" radius={[4, 4, 0, 0]} maxBarSize={36}>
                    <LabelList
                      dataKey="rawGap"
                      position="top"
                      formatter={(val: any) => (val != null ? `${val > 0 ? '+' : ''}${val}%` : '')}
                      style={{ fontSize: '9px', fontWeight: 700, fill: '#0B2545' }}
                    />
                    {formattedData.map((entry, index) => {
                      const isNegative = (entry.gapPct ?? 0) < 0;
                      const isPositive = (entry.gapPct ?? 0) > 0;
                      const color = isNegative ? '#EF4444' : isPositive ? '#10B981' : '#64748B';
                      return <Cell key={`cell-${index}`} fill={color} />;
                    })}
                  </Bar>
                </>
              )}

              {mode === 'raw' && (
                <>
                  <Bar dataKey="displayTarget" name="Policy Target Value" fill="#005A36" radius={[4, 4, 0, 0]} maxBarSize={32}>
                    <LabelList
                      dataKey="rawTarget"
                      position="top"
                      formatter={(val: any) => formatCalloutVal(val)}
                      style={{ fontSize: '9px', fontWeight: 700, fill: '#005A36' }}
                    />
                  </Bar>
                  <Bar dataKey="displayActual" name="Actual Output Value" fill="#D4AF37" radius={[4, 4, 0, 0]} maxBarSize={32}>
                    <LabelList
                      dataKey="rawActual"
                      position="top"
                      formatter={(val: any) => formatCalloutVal(val)}
                      style={{ fontSize: '9px', fontWeight: 700, fill: '#B45309' }}
                    />
                  </Bar>
                </>
              )}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

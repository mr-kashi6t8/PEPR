import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

export interface TimeSeriesDataPoint {
  date: string;
  value: number;
  benchmark?: number;
  value2?: number;
}

interface TrendLineChartProps {
  data?: TimeSeriesDataPoint[];
  color?: string;
  color2?: string;
  unit?: string;
  name1?: string;
  name2?: string;
}

export const TrendLineChart: React.FC<TrendLineChartProps> = ({
  data = [],
  color = '#005A36',
  color2 = '#0B2545',
  unit = '%',
  name1 = 'Primary Indicator',
  name2 = 'Comparison Indicator',
}) => {
  const [activePoint, setActivePoint] = React.useState<TimeSeriesDataPoint | null>(null);

  if (!data || data.length === 0) {
    return (
      <div className="w-full h-72 flex flex-col items-center justify-center bg-slate-50/50 rounded-xl border border-dashed border-slate-200 text-slate-400 text-xs italic gap-2">
        <span>Loading live time-series data from PostgreSQL database...</span>
      </div>
    );
  }

  const hasBenchmark = data.some((d) => d.benchmark !== undefined && d.benchmark !== null);
  const hasValue2 = data.some((d) => d.value2 !== undefined && d.value2 !== null);

  const displayPoint = activePoint || data[data.length - 1] || data[0];
  const showDots = data.length <= 40;

  return (
    <div className="w-full space-y-3">
      {/* Live Interactive Legend & Data Inspector Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#0B2545] text-white px-4 py-3 rounded-xl border-l-4 border-[#D4AF37] shadow-sm">
        <div className="flex items-center gap-2 font-mono">
          <span className="text-[#D4AF37] font-bold text-[11px] uppercase tracking-wider">
            {activePoint ? 'Inspecting Point:' : 'Latest Observation:'}
          </span>
          <span className="font-extrabold text-white text-sm bg-white/10 px-2 py-0.5 rounded">
            {displayPoint?.date || 'N/A'}
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-4 font-mono text-xs">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#005A36] inline-block"></span>
            <span className="text-slate-300">{name1}:</span>
            <span className="font-extrabold text-emerald-400 text-sm">
              {displayPoint?.value !== undefined ? Number(displayPoint.value).toFixed(2) : 'N/A'} {unit}
            </span>
          </div>

          {hasValue2 && (
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#60A5FA] inline-block"></span>
              <span className="text-slate-300">{name2}:</span>
              <span className="font-extrabold text-blue-300 text-sm">
                {displayPoint?.value2 !== undefined ? Number(displayPoint.value2).toFixed(2) : 'N/A'} {unit}
              </span>
            </div>
          )}

          {hasBenchmark && (
            <div className="flex items-center gap-1.5 border-l border-slate-700 pl-3">
              <span className="w-2.5 h-2.5 rounded-full bg-[#D4AF37] inline-block"></span>
              <span className="text-slate-300">Target Benchmark:</span>
              <span className="font-extrabold text-[#D4AF37] text-sm">
                {displayPoint?.benchmark !== undefined ? Number(displayPoint.benchmark).toFixed(2) : 'N/A'} {unit}
              </span>
            </div>
          )}

          {hasBenchmark && displayPoint?.value !== undefined && displayPoint?.benchmark !== undefined && (
            <div className="border-l border-slate-700 pl-3">
              <span className="text-slate-300 mr-1.5">Gap:</span>
              {(() => {
                const gap = Number(displayPoint.value) - Number(displayPoint.benchmark);
                return (
                  <span className={`font-extrabold text-sm ${gap > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
                    {gap > 0 ? `+${gap.toFixed(2)}` : gap.toFixed(2)} {unit}
                  </span>
                );
              })()}
            </div>
          )}
        </div>
      </div>

      {/* Chart Container */}
      <div className="w-full h-80 pt-1">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{ top: 15, right: 30, left: 15, bottom: 20 }}
            onMouseMove={(e: any) => {
              if (e && e.activePayload && e.activePayload.length > 0) {
                setActivePoint(e.activePayload[0].payload);
              }
            }}
            onMouseLeave={() => setActivePoint(null)}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11, fill: '#475569', fontWeight: 500 }}
              tickLine={{ stroke: '#CBD5E1' }}
              axisLine={{ stroke: '#CBD5E1' }}
              interval="preserveStartEnd"
              minTickGap={45}
              dy={8}
            />
            <YAxis
              tick={{ fontSize: 11, fill: '#475569', fontWeight: 500 }}
              tickLine={{ stroke: '#CBD5E1' }}
              axisLine={{ stroke: '#CBD5E1' }}
              domain={['auto', 'auto']}
              tickFormatter={(val) => `${val}${unit}`}
              dx={-4}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0B2545',
                borderColor: '#005A36',
                borderRadius: '10px',
                color: '#FFFFFF',
                fontSize: '12px',
                boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.4)',
                padding: '12px 16px',
              }}
              formatter={(val: any, name: any) => [
                `${Number(val).toFixed(2)} ${unit}`,
                String(name || ''),
              ]}
              labelFormatter={(label) => `Observation Period: ${label}`}
            />
            <Legend
              wrapperStyle={{ fontSize: '12px', paddingTop: '15px' }}
              iconType="circle"
            />
            <Line
              type="monotone"
              dataKey="value"
              name={name1}
              stroke={color}
              strokeWidth={3}
              dot={showDots ? { fill: color, r: 2.5, strokeWidth: 0 } : false}
              activeDot={{ r: 7, fill: color, stroke: '#FFFFFF', strokeWidth: 3 }}
            />
            {hasValue2 && (
              <Line
                type="monotone"
                dataKey="value2"
                name={name2}
                stroke={color2}
                strokeWidth={2.5}
                dot={showDots ? { fill: color2, r: 2.5, strokeWidth: 0 } : false}
                activeDot={{ r: 7, fill: color2, stroke: '#FFFFFF', strokeWidth: 3 }}
              />
            )}
            {hasBenchmark && (
              <Line
                type="monotone"
                dataKey="benchmark"
                name="Policy Target Benchmark"
                stroke="#D4AF37"
                strokeDasharray="6 4"
                strokeWidth={2}
                dot={false}
                activeDot={false}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

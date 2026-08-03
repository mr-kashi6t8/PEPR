import React, { useState, useEffect, useMemo } from 'react';
import { TrendingUp, Filter, Layers, AlertCircle, Calendar } from 'lucide-react';
import { useTrends, useAnomalies, useIndicators } from '../api/hooks';
import { Card, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { TrendLineChart } from '../components/charts/TrendLineChart';
import { api } from '../api/client';

export interface TimeSeriesDataPoint {
  date: string;
  value: number;
  benchmark?: number;
  value2?: number;
}

function matchesCategory(item: any, selectedCategory: string): boolean {
  if (selectedCategory === 'ALL') return true;
  const code = (item.indicator_code || item.code || '').toUpperCase();
  const name = (item.indicator_name || item.name || '').toLowerCase();
  const cat = (item.category || '').toLowerCase();

  if (selectedCategory === 'Inflation') {
    return cat.includes('inflation') || code.includes('CPI') || code.includes('SPI') || code.includes('WPI') || name.includes('price') || name.includes('inflation');
  }
  if (selectedCategory === 'Monetary Policy') {
    return cat.includes('monetary') || code.includes('POLICY') || code.includes('M2') || name.includes('rate') || name.includes('money');
  }
  if (selectedCategory === 'External Sector') {
    return cat.includes('external') || code.includes('RESERVES') || code.includes('CURRENT') || code.includes('USD') || code.includes('TRADE') || name.includes('trade') || name.includes('reserves') || name.includes('exchange');
  }
  if (selectedCategory === 'Capital Markets') {
    return cat.includes('capital') || cat.includes('market') || code.includes('PSX') || name.includes('psx') || name.includes('share') || name.includes('stock');
  }
  if (selectedCategory === 'Fiscal & Energy') {
    return cat.includes('fiscal') || cat.includes('energy') || code.includes('FBR') || code.includes('DEBT') || code.includes('GDP') || code.includes('TAX') || code.includes('UNEMPLOYMENT') || name.includes('tax') || name.includes('debt') || name.includes('gdp') || name.includes('unemployment');
  }
  return true;
}

function getDateKey(iso: string | null | undefined): string {
  if (!iso) return '';
  return iso.substring(0, 10);
}

function formatDateLabel(d: string): string {
  if (!d) return '';
  const dt = new Date(d + 'T00:00:00Z');
  return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
}

export const TrendsPage: React.FC = () => {
  // 'latest' = backend returns only the most-recent analysis run (within 4h window)
  // This is the meaningful default — shows the current pipeline's output only
  const [timeframe, setTimeframe] = useState<string>('latest');

  const { data: trendsRaw } = useTrends(timeframe);
  const { data: anomaliesRaw } = useAnomalies(timeframe);
  const { data: indicatorsRaw } = useIndicators();

  const trends = useMemo(() => {
    if (Array.isArray(trendsRaw)) return trendsRaw;
    if (trendsRaw && Array.isArray((trendsRaw as any).trends)) return (trendsRaw as any).trends;
    return [];
  }, [trendsRaw]);

  const anomalies = useMemo(() => {
    if (Array.isArray(anomaliesRaw)) return anomaliesRaw;
    if (anomaliesRaw && Array.isArray((anomaliesRaw as any).anomalies)) return (anomaliesRaw as any).anomalies;
    return [];
  }, [anomaliesRaw]);

  const indicators = useMemo(() => {
    if (Array.isArray(indicatorsRaw)) return indicatorsRaw;
    return [];
  }, [indicatorsRaw]);

  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [comparisonMode, setComparisonMode] = useState<boolean>(false);
  // Separate date selectors for trends and anomalies
  const [selectedTrendDate, setSelectedTrendDate] = useState<string>('');
  const [selectedAnomalyDate, setSelectedAnomalyDate] = useState<string>('');

  const [primaryIndicatorId, setPrimaryIndicatorId] = useState<string>('');
  const [secondaryIndicatorId, setSecondaryIndicatorId] = useState<string>('');

  const [chartData, setChartData] = useState<TimeSeriesDataPoint[]>([]);
  const [chartUnit, setChartUnit] = useState<string>('%');

  const categories = ['ALL', 'Inflation', 'Monetary Policy', 'External Sector', 'Capital Markets', 'Fiscal & Energy'];

  // Collect unique run dates from trends separately (sorted descending)
  const trendDates = useMemo(() => {
    const dateSet = new Set<string>();
    trends.forEach((t: any) => { const d = getDateKey(t.created_at); if (d) dateSet.add(d); });
    return Array.from(dateSet).sort((a, b) => b.localeCompare(a));
  }, [trends]);

  const anomalyDates = useMemo(() => {
    const dateSet = new Set<string>();
    anomalies.forEach((a: any) => { const d = getDateKey(a.detected_at || a.created_at); if (d) dateSet.add(d); });
    return Array.from(dateSet).sort((a, b) => b.localeCompare(a));
  }, [anomalies]);

  // Derive latest dates
  const latestTrendDate = trendDates[0] || '';
  const latestAnomalyDate = anomalyDates[0] || '';

  // Auto-select latest dates when data first loads
  useEffect(() => {
    if (latestTrendDate && !selectedTrendDate) setSelectedTrendDate(latestTrendDate);
  }, [latestTrendDate]);

  useEffect(() => {
    if (latestAnomalyDate && !selectedAnomalyDate) setSelectedAnomalyDate(latestAnomalyDate);
  }, [latestAnomalyDate]);

  const categoryIndicators = indicators.filter((ind) => matchesCategory(ind, selectedCategory));

  useEffect(() => {
    const list = categoryIndicators.length > 0 ? categoryIndicators : indicators;
    if (list.length > 0) {
      const currentValid = list.some((i) => i.id === primaryIndicatorId);
      if (!currentValid || !primaryIndicatorId) {
        setPrimaryIndicatorId(list[0].id);
      }
      if (list.length > 1 && (!secondaryIndicatorId || secondaryIndicatorId === list[0].id)) {
        setSecondaryIndicatorId(list[1].id);
      }
    }
  }, [selectedCategory, indicators]);

  useEffect(() => {
    let isMounted = true;
    async function loadHistory() {
      try {
        let activePrimaryId = primaryIndicatorId;
        let indList = indicators;

        if (!activePrimaryId) {
          if (indicators.length > 0) {
            const cpi = indicators.find((i: any) => i.code === 'PAK_CPI_YOY') || indicators[0];
            activePrimaryId = cpi.id;
          } else {
            const sumJson = await api.getIndicators();
            if (Array.isArray(sumJson) && sumJson.length > 0) {
              indList = sumJson;
              const cpi = sumJson.find((i: any) => i.code === 'PAK_CPI_YOY') || sumJson[0];
              activePrimaryId = cpi.id;
            }
          }
        }

        if (!activePrimaryId) return;

        const primaryHistory = await api.getIndicatorHistory(activePrimaryId);

        let secondaryHistory: Array<{ date: string; value: number }> = [];
        if (comparisonMode && secondaryIndicatorId) {
          secondaryHistory = await api.getIndicatorHistory(secondaryIndicatorId);
        }

        const primaryInd = indList.find((i: any) => i.id === activePrimaryId);

        let targetVal: number | undefined;
        if ((primaryInd as any)?.policy_gap?.target_value !== undefined) {
          targetVal = Number((primaryInd as any).policy_gap.target_value);
        } else {
          const code = ((primaryInd as any)?.code || '').toUpperCase();
          const name = ((primaryInd as any)?.name || '').toLowerCase();
          if (code.includes('CPI') || name.includes('cpi')) targetVal = 7.0;
          else if (code.includes('POLICY_RATE') || name.includes('rate') || name.includes('interest')) targetVal = 11.0;
          else if (code.includes('RESERVES') || name.includes('reserves')) targetVal = 13.5;
          else if (code.includes('KSE100') || name.includes('kse') || name.includes('psx')) targetVal = 85000.0;
          else if (code.includes('GDP') || name.includes('growth')) targetVal = 3.6;
          else if (code.includes('CIRCULAR') || name.includes('debt')) targetVal = 1.614;
          else if (code.includes('CURRENT_ACCOUNT') || name.includes('current account')) targetVal = -4.0;
          else if (code.includes('TRADE') || name.includes('trade')) targetVal = 30.0;
          else if (code.includes('USD') || name.includes('pkr') || name.includes('exchange')) targetVal = 280.0;
          else if (code.includes('UNEMPLOYMENT') || name.includes('unemployment')) targetVal = 6.3;
          else if (code.includes('TAX_GDP') || name.includes('tax')) targetVal = 11.5;
          else if (code.includes('TAX_REVENUE') || name.includes('revenue')) targetVal = 12.97;
          else if (code.includes('M2') || name.includes('money')) targetVal = 12.5;
          else if (code.includes('SPI') || name.includes('spi')) targetVal = 8.0;
          else if (code.includes('WPI') || name.includes('wpi')) targetVal = 8.5;
          else if (code.includes('PSX_ALL') || name.includes('all share')) targetVal = 55000.0;
          else if (code.includes('VOLUME') || name.includes('volume')) targetVal = 450.0;
          else targetVal = 10.0;
        }

        // Build chart points. Backend now deduplicates by month, but we keep
        // a Map here as a safety net for any edge cases (e.g. future daily indicators).
        const monthMap = new Map<string, TimeSeriesDataPoint>();
        primaryHistory.forEach((h: any, idx: number) => {
          const dateStr = h.date || (h.timestamp ? h.timestamp.substring(0, 7) : `P${idx + 1}`);
          monthMap.set(dateStr, {
            date: dateStr,
            value: Number(h.value),
            benchmark: targetVal !== undefined ? Number(targetVal) : undefined,
          });
        });
        const primaryPoints: TimeSeriesDataPoint[] = Array.from(monthMap.values());

        if (comparisonMode && secondaryHistory.length > 0) {
          secondaryHistory.forEach((h: any, idx: number) => {
            if (primaryPoints[idx]) {
              primaryPoints[idx].value2 = Number(h.value);
            }
          });
        }

        if (isMounted) {
          setChartData(primaryPoints);
          setChartUnit(primaryInd?.unit || '%');
        }
      } catch (err) {
        console.error('Error fetching live indicator history:', err);
      }
    }

    loadHistory();
    return () => { isMounted = false; };
  }, [primaryIndicatorId, secondaryIndicatorId, comparisonMode, indicators]);

  // Date-wise filter for trends — uses its own date selector
  const datewiseTrends = useMemo(() => {
    let base = trends.filter((t: any) => matchesCategory(t, selectedCategory));
    if (selectedTrendDate && selectedTrendDate !== 'all') {
      base = base.filter((t: any) => {
        const d = getDateKey(t.created_at);
        return d === selectedTrendDate;
      });
    }
    // Deduplicate: backend may store multiple runs per indicator.
    // Backend returns rows ordered by created_at DESC, so first occurrence = latest.
    const seen = new Set<string>();
    return base.filter((t: any) => {
      const key = String(t.indicator_id || t.id);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [trends, selectedCategory, selectedTrendDate]);

  // Date-wise filter for anomalies — uses its own date selector
  const datewiseAnomalies = useMemo(() => {
    let base = anomalies.filter((a: any) => matchesCategory(a, selectedCategory));
    if (selectedAnomalyDate && selectedAnomalyDate !== 'all') {
      base = base.filter((a: any) => {
        const d = getDateKey(a.detected_at || a.created_at);
        return d === selectedAnomalyDate;
      });
    }
    // Deduplicate by indicator_id (or observation_id), keeping latest
    const seen = new Set<string>();
    return base.filter((a: any) => {
      const key = String(a.indicator_id || a.observation_id || a.id);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [anomalies, selectedCategory, selectedAnomalyDate]);

  const primaryIndObj = indicators.find((i) => i.id === primaryIndicatorId);
  const secondaryIndObj = indicators.find((i) => i.id === secondaryIndicatorId);

  const trendDateLabel = selectedTrendDate === 'all' ? 'All Dates' : selectedTrendDate ? formatDateLabel(selectedTrendDate) : 'Loading…';
  const anomalyDateLabel = selectedAnomalyDate === 'all' ? 'All Dates' : selectedAnomalyDate ? formatDateLabel(selectedAnomalyDate) : 'Loading…';
  const isLatestTrendDate = selectedTrendDate === latestTrendDate && latestTrendDate !== '';
  const isLatestAnomalyDate = selectedAnomalyDate === latestAnomalyDate && latestAnomalyDate !== '';

  return (
    <div className="space-y-6">
      {/* Page Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold font-serif text-[#0B2545]">
            Statistical Trends & Machine Learning Anomalies
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Real-time statistical trendlines, moving average convergence, and IsolationForest ML anomaly detection.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Category Filter */}
          <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-lg border border-slate-200 text-xs shadow-sm">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-transparent font-medium text-slate-700 focus:outline-none"
            >
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat} Category
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => setComparisonMode(!comparisonMode)}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold border transition-all shadow-sm ${comparisonMode
              ? 'bg-[#005A36] text-white border-[#005A36]'
              : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
              }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Comparison Mode {comparisonMode ? 'ON' : 'OFF'}</span>
          </button>
        </div>
      </div>

      {/* Main Time Series Chart */}
      <Card accentBorder>
        <CardHeader>
          <div className="flex flex-col md:flex-row md:items-center justify-between w-full gap-4">
            <div>
              <CardTitle>
                <TrendingUp className="w-5 h-5 text-[#005A36]" />
                <span>Live Time-Series Chart: {primaryIndObj?.name || 'Consumer Price Index'}</span>
              </CardTitle>
              <CardDescription>
                Live PostgreSQL observation time series vs official target benchmarks
              </CardDescription>
            </div>

            <div className="flex items-center gap-3">
              <select
                value={primaryIndicatorId}
                onChange={(e) => setPrimaryIndicatorId(e.target.value)}
                className="bg-slate-50 border border-slate-300 text-xs rounded-lg px-2.5 py-1.5 font-bold text-[#0B2545] focus:outline-none"
              >
                {(categoryIndicators.length > 0 ? categoryIndicators : indicators).map((ind) => (
                  <option key={ind.id} value={ind.id}>
                    {ind.name} ({ind.code})
                  </option>
                ))}
              </select>

              {comparisonMode && (
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-400">vs</span>
                  <select
                    value={secondaryIndicatorId}
                    onChange={(e) => setSecondaryIndicatorId(e.target.value)}
                    className="bg-slate-50 border border-slate-300 text-xs rounded-lg px-2.5 py-1.5 font-bold text-[#0B2545] focus:outline-none"
                  >
                    {(categoryIndicators.length > 0 ? categoryIndicators : indicators).map((ind) => (
                      <option key={ind.id} value={ind.id}>
                        {ind.name} ({ind.code})
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          </div>
        </CardHeader>

        <div className="p-4">
          <TrendLineChart
            data={chartData}
            unit={chartUnit}
            color="#005A36"
            color2="#0B2545"
            name1={primaryIndObj?.name || 'Primary Indicator'}
            name2={secondaryIndObj?.name || 'Secondary Indicator'}
          />
        </div>
      </Card>

      {/* Machine Learning Anomalies Section */}
      <div className="bg-amber-50/80 border border-amber-200/90 rounded-xl p-4 flex items-start gap-3 shadow-sm">
        <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
        <div className="w-full">
          <div className="flex flex-wrap justify-between items-center gap-2">
            <h3 className="text-xs font-bold text-amber-900 uppercase tracking-wider">
              Machine Learning Outliers &amp; Anomalies ({datewiseAnomalies.length})
              <span className="ml-2 font-normal text-amber-700 border-l border-amber-300 pl-2">
                {isLatestAnomalyDate ? '⚡ Latest Run' : anomalyDateLabel}
              </span>
            </h3>
            <div className="flex items-center gap-2">
              <Calendar className="w-3.5 h-3.5 text-amber-600" />
              <select
                value={selectedAnomalyDate}
                onChange={(e) => setSelectedAnomalyDate(e.target.value)}
                className="bg-amber-50 border border-amber-200 rounded-md text-[11px] px-2 py-0.5 font-semibold text-amber-900 focus:outline-none"
              >
                {anomalyDates.length === 0 && <option value="">Loading…</option>}
                {anomalyDates.map((d, idx) => (
                  <option key={d} value={d}>{formatDateLabel(d)}{idx === 0 ? ' ⚡' : ''}</option>
                ))}
                <option value="all">— All Dates —</option>
              </select>
              <span className="text-[10px] text-amber-700 font-medium">IsolationForest &amp; Z-Score</span>
            </div>
          </div>

          {datewiseAnomalies.length === 0 ? (
            <p className="text-xs text-amber-800 italic mt-2">No anomalies flagged for {anomalyDateLabel}.</p>
          ) : (
            <div className="mt-3 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {datewiseAnomalies.map((an: any) => {
                const matchedInd = indicators.find((i) => i.id === an.indicator_id);
                const indName = matchedInd?.name || an.indicator_name || 'Economic Indicator';
                const score = typeof an.anomaly_score === 'number' ? an.anomaly_score : 3.25;

                return (
                  <div key={an.id} className="bg-white p-3 rounded-lg border border-amber-200/80 text-xs shadow-xs">
                    <div className="flex justify-between items-start font-bold text-[#0B2545]">
                      <span className="truncate max-w-[180px]">{indName}</span>
                      <Badge variant="critical">Score: {score.toFixed(2)}</Badge>
                    </div>
                    <p className="text-slate-600 mt-1.5 text-[11px]">
                      Algorithm: <span className="font-semibold text-slate-800">{an.algorithm_used || 'IsolationForest (MoM)'}</span>
                    </p>
                    <p className="text-[10px] text-slate-400 mt-1 font-mono">
                      Detected: {an.detected_at ? new Date(an.detected_at).toLocaleDateString() : 'Recent'}
                    </p>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Statistical Trends Grid */}
      <div>
        <div className="flex flex-wrap justify-between items-center mb-3 gap-2">
          <h2 className="text-lg font-bold text-[#0B2545]">
            Evaluated Statistical Trends ({datewiseTrends.length})
          </h2>
          <div className="flex items-center gap-2">
            <Calendar className="w-3.5 h-3.5 text-[#005A36]" />
            <select
              value={selectedTrendDate}
              onChange={(e) => {
                const val = e.target.value;
                setSelectedTrendDate(val);
                // Switching to "All Dates" needs the full dataset from backend
                if (val === 'all') setTimeframe('all');
                else setTimeframe('latest');
              }}
              className="bg-emerald-50 border border-emerald-200 rounded-md text-[11px] px-2 py-0.5 font-semibold text-emerald-900 focus:outline-none"
            >
              {trendDates.length === 0 && <option value="">Loading…</option>}
              {trendDates.map((d, idx) => (
                <option key={d} value={d}>{formatDateLabel(d)}{idx === 0 ? ' ⚡ Latest' : ''}</option>
              ))}
              <option value="all">— All Ingestion Dates —</option>
            </select>
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-md border ${isLatestTrendDate
              ? 'text-emerald-700 bg-emerald-50 border-emerald-200'
              : 'text-slate-600 bg-slate-100 border-slate-200'
              }`}>
              {isLatestTrendDate ? '⚡ Latest Run' : trendDateLabel}
            </span>
          </div>
        </div>

        {datewiseTrends.length === 0 ? (
          <p className="text-xs text-slate-400 italic">
            No statistical trends found for {trendDateLabel}. Try selecting a different ingestion date.
          </p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {datewiseTrends.map((trend: any) => {
              const matchedInd = indicators.find((i) => i.id === trend.indicator_id);
              const name = matchedInd?.name || trend.indicator_name || 'Indicator';
              const direction = trend.trend_direction || trend.direction || 'flat';
              const severity = trend.severity || 'low';
              const pct = trend.pct_change !== undefined ? trend.pct_change : (trend.percentage_change || 0);
              const runDate = trend.created_at ? formatDateLabel(getDateKey(trend.created_at)) : 'Latest';

              return (
                <Card key={trend.id} hoverable>
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-[10px] font-bold text-emerald-700 tracking-wider bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200/60">
                        Run: {runDate}
                      </span>
                      <h3 className="text-base font-bold text-[#0B2545] mt-1">{name}</h3>
                    </div>
                    <Badge variant={severity.toLowerCase() as any}>{severity}</Badge>
                  </div>

                  <div className="mt-4 grid grid-cols-3 gap-2 bg-slate-50 p-3 rounded-lg text-center border border-slate-100">
                    <div>
                      <p className="text-[10px] text-slate-400 uppercase font-semibold">Current</p>
                      <p className="text-sm font-bold font-mono text-[#0B2545]">{Number(trend.current_value).toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-400 uppercase font-semibold">Shift %</p>
                      <p className={`text-sm font-bold font-mono ${pct > 0 ? 'text-red-600' : pct < 0 ? 'text-emerald-600' : 'text-slate-600'}`}>
                        {pct > 0 ? '+' : ''}{Number(pct).toFixed(2)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-400 uppercase font-semibold">Direction</p>
                      <p className={`text-sm font-bold font-mono uppercase ${direction === 'upward' ? 'text-red-600' : direction === 'downward' ? 'text-emerald-600' : 'text-slate-500'}`}>
                        {direction}
                      </p>
                    </div>
                  </div>

                  <div className="mt-3 text-[11px] text-slate-500">
                    Period: {trend.period || 'N/A'}
                  </div>

                  {trend.forecast_30d && (
                    <div className="mt-3 p-2.5 bg-emerald-50/70 border border-emerald-200/80 rounded-md">
                      <div className="flex justify-between items-center text-[11px] font-bold text-emerald-900 mb-1">
                        <span className="flex items-center gap-1 text-emerald-800">⚡ 30-Day Forecast Corridor</span>
                        <span className="font-mono text-emerald-700 font-semibold">Expected: {trend.forecast_30d.expected}</span>
                      </div>
                      <div className="flex justify-between items-center text-[10px] text-slate-600 font-mono mt-1">
                        <span>Min: {trend.forecast_30d.min_corridor}</span>
                        <div className="w-1/3 bg-emerald-200 h-1.5 rounded-full overflow-hidden mx-2">
                          <div className="bg-emerald-600 h-full rounded-full w-2/3" />
                        </div>
                        <span>Max: {trend.forecast_30d.max_corridor}</span>
                      </div>
                    </div>
                  )}

                  <div className="mt-2 flex justify-between items-center text-xs text-slate-500">
                    <span className="text-[11px]">Engine: {trend.detection_method || 'Statistical Score'}</span>
                    <span className="font-mono text-[10px] text-slate-400">
                      Confidence: {((trend.confidence_score || 0.85) * 100).toFixed(0)}%
                    </span>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

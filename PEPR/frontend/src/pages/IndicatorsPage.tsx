import React, { useState, useMemo } from 'react';
import { ArrowUpRight, ArrowDownRight, Filter } from 'lucide-react';
import { useIndicators } from '../api/hooks';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

export const IndicatorsPage: React.FC = () => {
  const { data: indicators = [] } = useIndicators();
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');

  // Dynamically extract all unique categories present in the indicators array from backend API
  const categories = useMemo(() => {
    const set = new Set<string>();
    set.add('ALL');
    
    // Explicit primary category order for structure
    const primary = ['Macroeconomic', 'Commodities & Energy', 'Financial & Stocks', 'Fiscal & Tax'];
    primary.forEach((c) => set.add(c));

    indicators.forEach((ind: any) => {
      if (ind.category && typeof ind.category === 'string') {
        const trimmed = ind.category.trim();
        if (trimmed) set.add(trimmed);
      }
    });

    return Array.from(set);
  }, [indicators]);

  const filteredIndicators = indicators.filter((ind: any) => {
    if (selectedCategory === 'ALL') return true;
    const cat = (ind.category || 'Macroeconomic').toLowerCase();
    const sel = selectedCategory.toLowerCase();

    // 1. Direct exact or substring match for dynamic categories returned by backend API
    if (cat === sel || cat.includes(sel) || sel.includes(cat)) return true;

    // 2. Heuristic domain match for dynamic sources
    const code = (ind.code || '').toUpperCase();
    const name = (ind.name || '').toLowerCase();

    if (sel.includes('commodit') || sel.includes('energy')) {
      return (
        cat.includes('commodity') ||
        cat.includes('energy') ||
        code.includes('GOLD') ||
        code.includes('FUEL') ||
        code.includes('CRUDE') ||
        code.includes('PETROL') ||
        code.includes('DIESEL') ||
        code.includes('COMM') ||
        name.includes('gold') ||
        name.includes('petrol') ||
        name.includes('diesel') ||
        name.includes('fuel') ||
        name.includes('crude') ||
        name.includes('oil') ||
        name.includes('bullion') ||
        name.includes('tola')
      );
    }
    if (sel.includes('financial') || sel.includes('stock') || sel.includes('market')) {
      return cat.includes('capital') || cat.includes('monetary') || code.includes('PSX') || code.includes('SBP') || code.includes('RATE') || name.includes('psx') || name.includes('stock');
    }
    if (sel.includes('fiscal') || sel.includes('tax')) {
      return cat.includes('fiscal') || code.includes('FBR') || code.includes('TAX') || name.includes('tax') || name.includes('revenue');
    }
    if (sel.includes('macro')) {
      return !cat.includes('commodity') && !cat.includes('energy') && !code.includes('GOLD') && !code.includes('PETROL');
    }
    return false;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold font-serif text-[#0B2545]">
            Economic & Commodities Indicators Directory (M1)
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Catalog of macroeconomic, gold, fuel, petroleum, crude oil, and energy indicators ingested live from SBP, PBS, PSX, World Bank, OGRA, Sarafa Bullion Market, and Commodity Feeds.
          </p>
        </div>

        {/* Category Filters */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
          <Filter className="w-4 h-4 text-slate-400 mr-1 flex-shrink-0" />
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
                selectedCategory === cat
                  ? 'bg-[#0B2545] text-white shadow-sm'
                  : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredIndicators.map((ind: any) => {
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

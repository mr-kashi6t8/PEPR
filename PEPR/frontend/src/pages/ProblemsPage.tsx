import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowUpRight, Search, Award } from 'lucide-react';
import { useProblems } from '../api/hooks';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';

export const ProblemsPage: React.FC = () => {
  const { data: problems = [] } = useProblems();
  const [categoryFilter, setCategoryFilter] = useState('ALL');

  const categories = ['ALL', 'Commodities & Energy', 'Inflation & Prices', 'Fiscal Policy & Tax', 'Monetary Policy & Rates', 'Trade & Exports'];

  const filtered = problems.filter((prob) => {
    const text = (prob.title + ' ' + prob.description).toLowerCase();
    const matchesSearch = text.includes(search.toLowerCase());
    const matchesSev = severityFilter === 'ALL' || prob.severity === severityFilter;

    let matchesCat = true;
    if (categoryFilter !== 'ALL') {
      const catSel = categoryFilter.toLowerCase();
      if (catSel.includes('commodit') || catSel.includes('energy')) {
        matchesCat = text.includes('gold') || text.includes('petrol') || text.includes('diesel') || text.includes('fuel') || text.includes('crude') || text.includes('power') || text.includes('electricity') || text.includes('tariff') || text.includes('energy');
      } else if (catSel.includes('inflation') || catSel.includes('price')) {
        matchesCat = text.includes('inflation') || text.includes('cpi') || text.includes('price') || text.includes('cost') || text.includes('food');
      } else if (catSel.includes('fiscal') || catSel.includes('tax')) {
        matchesCat = text.includes('tax') || text.includes('fbr') || text.includes('revenue') || text.includes('budget') || text.includes('fiscal');
      } else if (catSel.includes('monetary') || catSel.includes('rate')) {
        matchesCat = text.includes('sbp') || text.includes('interest') || text.includes('rate') || text.includes('rupee') || text.includes('forex');
      } else if (catSel.includes('trade') || catSel.includes('export')) {
        matchesCat = text.includes('trade') || text.includes('export') || text.includes('import') || text.includes('psx');
      }
    }

    return matchesSearch && matchesSev && matchesCat;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold font-serif text-[#0B2545]">
              Emerging Economic Problems Radar
            </h1>
            <span className="text-xs font-bold bg-[#005A36] text-white px-2.5 py-0.5 rounded-full font-mono">
              {filtered.length} Active Problems (Top 10 First)
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Prioritized economic problems synthesized from 7-day database window analysis (M1-M4 across macro, commodities, fuel, and energy), enriched with M5 PIDE Research Showcase publications.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="relative w-56">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search problems..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-1.5 text-xs bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#005A36]/30"
            />
          </div>

          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-3 py-1.5 text-xs bg-white border border-slate-200 rounded-lg font-medium text-slate-700"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
          </select>
        </div>
      </div>

      {/* Category Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setCategoryFilter(cat)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
              categoryFilter === cat
                ? 'bg-[#005A36] text-white shadow-sm'
                : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Problems List */}
      <div className="space-y-4">
        {filtered.map((prob, idx) => {
          const isTop10 = idx < 10;
          return (
            <Card key={prob.id} hoverable accentBorder={isTop10}>
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-2 max-w-3xl">
                  <div className="flex flex-wrap items-center gap-2">
                    {isTop10 ? (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold bg-amber-500 text-white px-2 py-0.5 rounded font-mono shadow-sm">
                        <Award className="w-3 h-3" />
                        TOP 10 RANK #{idx + 1}
                      </span>
                    ) : (
                      <span className="text-[10px] font-bold bg-slate-200 text-slate-700 px-2 py-0.5 rounded font-mono">
                        RANK #{idx + 1}
                      </span>
                    )}

                    <Badge variant={prob.severity.toLowerCase() as any}>
                      {prob.severity}
                    </Badge>
                    <span className="text-xs text-slate-400">• Created: {new Date(prob.created_at).toLocaleDateString()}</span>
                  </div>

                  <Link
                    to={`/problems/${prob.id}`}
                    className="text-lg font-bold text-[#0B2545] hover:text-[#005A36] transition-colors block font-serif"
                  >
                    {prob.title}
                  </Link>

                  <p className="text-xs text-slate-600 line-clamp-2">{prob.description}</p>

                  <div className="flex flex-wrap gap-2 pt-1">
                    {prob.affected_indicators.map((ind) => (
                      <span
                        key={ind}
                        className="px-2 py-0.5 bg-slate-100 text-[#005A36] rounded text-[10px] font-mono font-bold border border-slate-200"
                      >
                        {ind}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Priority Score Box */}
                <div className="flex flex-col items-end justify-center min-w-[150px] p-4 bg-slate-50 rounded-xl border border-slate-200/80">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    Priority Score
                  </span>
                  <span className="text-3xl font-extrabold font-mono text-[#005A36]">
                    {prob.priority_score.toFixed(1)}
                  </span>
                  <span className="text-[10px] text-slate-500 mt-1">
                    Confidence: {(prob.confidence_score * 100).toFixed(0)}%
                  </span>
                  <Link to={`/problems/${prob.id}`} className="mt-3">
                    <Button size="sm" variant="primary" icon={<ArrowUpRight className="w-3.5 h-3.5" />}>
                      Deep Dive
                    </Button>
                  </Link>
                </div>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
};

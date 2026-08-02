import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import {
  Menu,
  Search,
  Bell,
  RefreshCw,
  ShieldCheck,
  User,
  LogOut,
  ChevronDown,
  KeyRound,
  CheckCircle2,
} from 'lucide-react';
import { useAuth, type UserRole } from '../../context/AuthContext';
import { useAlerts, useIndicators, useResearchPapers, usePolicyGaps, useProblems } from '../../api/hooks';

interface HeaderProps {
  onToggleSidebar: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onToggleSidebar }) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user, logout, isAuthenticated } = useAuth();
  
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  // Manual Data Refresh State
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshToast, setRefreshToast] = useState<string | null>(null);

  // Live Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  // Queries for live search
  const { data: alerts = [] } = useAlerts();
  const { data: indicators = [] } = useIndicators();
  const { data: papers = [] } = useResearchPapers();
  const { data: gaps = [] } = usePolicyGaps();
  const { data: problems = [] } = useProblems();

  const unreadAlerts = alerts.filter((a) => !a.is_read).length;

  // Filter search results
  const matchingIndicators = searchQuery
    ? indicators.filter(
        (i) =>
          i.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          i.code.toLowerCase().includes(searchQuery.toLowerCase())
      ).slice(0, 3)
    : [];

  const matchingPapers = searchQuery
    ? papers.filter(
        (p) =>
          p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          (p.document_identifier && p.document_identifier.toLowerCase().includes(searchQuery.toLowerCase()))
      ).slice(0, 3)
    : [];

  const matchingGaps = searchQuery
    ? gaps.filter(
        (g) =>
          g.target?.target_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          g.gap_status?.toLowerCase().includes(searchQuery.toLowerCase())
      ).slice(0, 3)
    : [];

  const matchingProblems = searchQuery
    ? problems.filter((p) => p.title.toLowerCase().includes(searchQuery.toLowerCase())).slice(0, 3)
    : [];

  const hasSearchResults =
    matchingIndicators.length > 0 ||
    matchingPapers.length > 0 ||
    matchingGaps.length > 0 ||
    matchingProblems.length > 0;

  // Close search dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsSearchOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleManualRefresh = async () => {
    setIsRefreshing(true);
    setRefreshToast('Refreshing live database and analytics cache...');
    
    try {
      await queryClient.invalidateQueries();
      setTimeout(() => {
        setIsRefreshing(false);
        setRefreshToast('Database cache updated! All screens refreshed.');
        setTimeout(() => setRefreshToast(null), 3000);
      }, 800);
    } catch (e) {
      setIsRefreshing(false);
      setRefreshToast(null);
    }
  };

  const roleBadgeColors: Record<UserRole, { bg: string; text: string; border: string }> = {
    RESEARCHER: { bg: 'bg-emerald-50', text: 'text-[#005A36]', border: 'border-emerald-200' },
    MANAGEMENT: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
    ICT: { bg: 'bg-amber-50', text: 'text-amber-800', border: 'border-amber-200' },
    ADMIN: { bg: 'bg-purple-50', text: 'text-purple-800', border: 'border-purple-200' },
  };

  const currentRole = user?.role || 'RESEARCHER';

  return (
    <>
      <header className="sticky top-0 z-30 h-16 bg-white border-b border-slate-200/90 px-4 lg:px-6 flex items-center justify-between shadow-2xs">
        {/* Left Side: Mobile Menu & Live Search */}
        <div className="flex items-center gap-4">
          <button
            onClick={onToggleSidebar}
            className="p-2 text-slate-600 hover:text-slate-900 rounded-lg lg:hidden"
            aria-label="Toggle Navigation"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Interactive Live Search Bar */}
          <div ref={searchRef} className="relative hidden md:block w-80">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search indicators, papers, policy gaps..."
                value={searchQuery}
                onFocus={() => setIsSearchOpen(true)}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setIsSearchOpen(true);
                }}
                className="w-full pl-9 pr-8 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#005A36]/30 focus:border-[#005A36] transition-all"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-xs text-slate-400 hover:text-slate-600"
                >
                  ✕
                </button>
              )}
            </div>

            {/* Live Search Autocomplete Dropdown */}
            {isSearchOpen && searchQuery && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-slate-200 rounded-xl shadow-2xl overflow-hidden z-50 text-xs">
                {hasSearchResults ? (
                  <div className="max-h-96 overflow-y-auto divide-y divide-slate-100">
                    {/* Indicators */}
                    {matchingIndicators.length > 0 && (
                      <div className="p-2">
                        <div className="text-[10px] font-bold text-slate-400 uppercase px-2 mb-1">Indicators</div>
                        {matchingIndicators.map((ind) => (
                          <div
                            key={ind.id}
                            onClick={() => {
                              navigate('/indicators');
                              setIsSearchOpen(false);
                            }}
                            className="p-2 hover:bg-slate-50 rounded-lg cursor-pointer flex items-center justify-between"
                          >
                            <span className="font-semibold text-slate-800">{ind.name}</span>
                            <span className="font-mono text-[10px] text-slate-400">{ind.code}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Research Papers */}
                    {matchingPapers.length > 0 && (
                      <div className="p-2">
                        <div className="text-[10px] font-bold text-slate-400 uppercase px-2 mb-1">PIDE Research</div>
                        {matchingPapers.map((paper) => (
                          <div
                            key={paper.id}
                            onClick={() => {
                              navigate('/research');
                              setIsSearchOpen(false);
                            }}
                            className="p-2 hover:bg-slate-50 rounded-lg cursor-pointer"
                          >
                            <div className="font-semibold text-[#0369a1] line-clamp-1">{paper.title}</div>
                            <div className="text-[10px] text-slate-400">{paper.document_identifier}</div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Policy Gaps */}
                    {matchingGaps.length > 0 && (
                      <div className="p-2">
                        <div className="text-[10px] font-bold text-slate-400 uppercase px-2 mb-1">Policy Gaps</div>
                        {matchingGaps.map((gap) => (
                          <div
                            key={gap.id}
                            onClick={() => {
                              navigate('/gaps');
                              setIsSearchOpen(false);
                            }}
                            className="p-2 hover:bg-slate-50 rounded-lg cursor-pointer flex items-center justify-between"
                          >
                            <span className="font-semibold text-slate-800">{gap.target?.target_name}</span>
                            <span className="text-[10px] font-bold text-red-600">{gap.gap_status}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Problems */}
                    {matchingProblems.length > 0 && (
                      <div className="p-2">
                        <div className="text-[10px] font-bold text-slate-400 uppercase px-2 mb-1">Emerging Problems</div>
                        {matchingProblems.map((prob) => (
                          <div
                            key={prob.id}
                            onClick={() => {
                              navigate('/problems');
                              setIsSearchOpen(false);
                            }}
                            className="p-2 hover:bg-slate-50 rounded-lg cursor-pointer font-semibold text-slate-800"
                          >
                            {prob.title}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="p-4 text-center text-slate-500">No matching items found for "{searchQuery}".</div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Side Controls */}
        <div className="flex items-center gap-3">
          {/* Status Badge */}
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 bg-emerald-50 text-[#005A36] text-xs font-semibold rounded-full border border-emerald-200">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Real Database Synchronized</span>
          </div>

          {/* Alerts Button */}
          <button
            onClick={() => navigate('/alerts')}
            className="relative p-2 text-slate-600 hover:text-[#005A36] hover:bg-slate-50 rounded-lg transition-colors"
            title="System Alerts"
          >
            <Bell className="w-5 h-5" />
            {unreadAlerts > 0 && (
              <span className="absolute top-1.5 right-1.5 w-4 h-4 bg-red-600 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                {unreadAlerts}
              </span>
            )}
          </button>

          {/* Manual Refresh Button */}
          <button
            onClick={handleManualRefresh}
            disabled={isRefreshing}
            className={`p-2 text-slate-600 hover:text-[#005A36] hover:bg-slate-50 rounded-lg transition-colors ${
              isRefreshing ? 'animate-spin text-[#005A36]' : ''
            }`}
            title="Refetch Live Database & Analytics"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          <div className="h-6 w-px bg-slate-200 mx-1" />

          {/* Interactive User Profile Avatar & Dropdown */}
          <div className="relative">
            <button
              onClick={() => setIsProfileOpen(!isProfileOpen)}
              className="flex items-center gap-2 p-1.5 rounded-xl hover:bg-slate-50 border border-transparent hover:border-slate-200 transition-all"
            >
              <div className="w-8 h-8 rounded-full bg-[#005A36] text-white flex items-center justify-center font-bold text-xs shadow-xs">
                {user?.full_name ? user.full_name.slice(0, 2).toUpperCase() : 'PIDE'}
              </div>
              <div className="hidden xl:block text-left">
                <p className="text-xs font-bold text-[#0B2545] leading-none">
                  {user?.full_name || 'PIDE Member'}
                </p>
                <div className="flex items-center gap-1 mt-0.5">
                  <span
                    className={`text-[9px] font-bold px-1.5 py-0.2 rounded border ${roleBadgeColors[currentRole].bg} ${roleBadgeColors[currentRole].text} ${roleBadgeColors[currentRole].border}`}
                  >
                    {currentRole}
                  </span>
                </div>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 hidden xl:block" />
            </button>

            {/* Profile Menu Dropdown */}
            {isProfileOpen && (
              <div className="absolute right-0 mt-2 w-64 bg-white border border-slate-200 rounded-2xl shadow-2xl p-3 z-50 animate-fadeIn text-xs">
                <div className="p-3 bg-slate-50 rounded-xl mb-3 border border-slate-100">
                  <div className="font-bold text-[#0B2545] text-sm">{user?.full_name || 'Guest User'}</div>
                  <div className="text-[11px] text-slate-500 font-mono">{user?.email || 'guest@pide.org.pk'}</div>
                  <div className="mt-2 flex items-center justify-between">
                    <span className="text-[10px] text-slate-400 font-bold uppercase">Active Role:</span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded border ${roleBadgeColors[currentRole].bg} ${roleBadgeColors[currentRole].text} ${roleBadgeColors[currentRole].border}`}
                    >
                      {currentRole}
                    </span>
                  </div>
                </div>

                <div className="space-y-1 pt-2 border-t border-slate-100">
                  <button
                    onClick={() => {
                      navigate('/forgot-password');
                      setIsProfileOpen(false);
                    }}
                    className="w-full flex items-center gap-2 p-2 hover:bg-slate-50 rounded-lg text-slate-700 font-medium text-left"
                  >
                    <KeyRound className="w-4 h-4 text-slate-400" />
                    <span>Forgot Password Page</span>
                  </button>

                  {isAuthenticated ? (
                    <button
                      onClick={() => {
                        logout();
                        navigate('/login');
                        setIsProfileOpen(false);
                      }}
                      className="w-full flex items-center gap-2 p-2 hover:bg-red-50 text-red-600 rounded-lg font-bold text-left"
                    >
                      <LogOut className="w-4 h-4 text-red-500" />
                      <span>Log Out</span>
                    </button>
                  ) : (
                    <button
                      onClick={() => {
                        navigate('/login');
                        setIsProfileOpen(false);
                      }}
                      className="w-full flex items-center gap-2 p-2 hover:bg-emerald-50 text-[#005A36] rounded-lg font-bold text-left"
                    >
                      <User className="w-4 h-4" />
                      <span>Sign In Page</span>
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Refresh Toast Notification */}
      {refreshToast && (
        <div className="fixed bottom-4 right-4 z-50 p-3 bg-slate-900 text-white text-xs font-semibold rounded-xl shadow-2xl flex items-center gap-2 border border-slate-700 animate-slideUp">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{refreshToast}</span>
        </div>
      )}
    </>
  );
};

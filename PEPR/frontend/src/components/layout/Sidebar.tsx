import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  TrendingUp,
  GitCompare,
  AlertTriangle,
  BookOpen,
  FileText,
  Activity,
  Bell,
  Sliders,
  Settings,
  ShieldCheck,
  Users,
} from 'lucide-react';
import { useAuth, type UserRole } from '../../context/AuthContext';
import { PIDELogo } from '../PIDELogo';

interface SidebarProps {
  isOpen: boolean;
  onClose?: () => void;
}

interface NavItem {
  name: string;
  path: string;
  icon: React.ElementType;
  allowedRoles?: UserRole[];
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen }) => {
  const { user } = useAuth();
  const currentRole: UserRole = user?.role || 'RESEARCHER';

  const allNavItems: NavItem[] = [
    {
      name: 'Dashboard',
      path: '/dashboard',
      icon: LayoutDashboard,
      allowedRoles: ['RESEARCHER', 'MANAGEMENT', 'ICT', 'ADMIN'],
    },
    {
      name: 'Trends Analysis',
      path: '/trends',
      icon: TrendingUp,
      allowedRoles: ['RESEARCHER', 'ICT', 'ADMIN'],
    },
    {
      name: 'Policy Target Gaps',
      path: '/gaps',
      icon: GitCompare,
      allowedRoles: ['RESEARCHER', 'MANAGEMENT', 'ADMIN'],
    },
    {
      name: 'Emerging Problems',
      path: '/problems',
      icon: AlertTriangle,
      allowedRoles: ['RESEARCHER', 'MANAGEMENT', 'ADMIN'],
    },
    {
      name: 'PIDE Research Showcase',
      path: '/research',
      icon: BookOpen,
      allowedRoles: ['RESEARCHER', 'ADMIN'],
    },
    {
      name: 'Weekly Reports',
      path: '/reports',
      icon: FileText,
      allowedRoles: ['RESEARCHER', 'MANAGEMENT', 'ADMIN'],
    },
    {
      name: 'Macro Indicators',
      path: '/indicators',
      icon: Activity,
      allowedRoles: ['RESEARCHER', 'MANAGEMENT', 'ICT', 'ADMIN'],
    },
    {
      name: 'System Alerts',
      path: '/alerts',
      icon: Bell,
      allowedRoles: ['RESEARCHER', 'ICT', 'ADMIN'],
    },
    {
      name: 'Data Pipelines',
      path: '/admin',
      icon: Sliders,
      allowedRoles: ['ICT', 'ADMIN'],
    },
    {
      name: 'Users & Roles',
      path: '/users',
      icon: Users,
      allowedRoles: ['ADMIN'],
    },
    {
      name: 'Settings',
      path: '/settings',
      icon: Settings,
      allowedRoles: ['ADMIN'],
    },
  ];

  // Filter navigation items specifically for the active user role
  const filteredNavItems = allNavItems.filter(
    (item) => !item.allowedRoles || item.allowedRoles.includes(currentRole)
  );

  const roleLabels: Record<UserRole, { label: string; badgeBg: string; border: string }> = {
    RESEARCHER: { label: 'Policy Economist', badgeBg: 'bg-emerald-500/20 text-emerald-300', border: 'border-emerald-500/40' },
    MANAGEMENT: { label: 'Executive Directorate', badgeBg: 'bg-blue-500/20 text-blue-300', border: 'border-blue-500/40' },
    ICT: { label: 'ICT Operations Team', badgeBg: 'bg-amber-500/20 text-amber-300', border: 'border-amber-500/40' },
    ADMIN: { label: 'System Administrator', badgeBg: 'bg-purple-500/20 text-purple-300', border: 'border-purple-500/40' },
  };

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 w-64 bg-[#0B2545] text-slate-200 border-r border-[#071930] transform transition-transform duration-200 ease-in-out lg:translate-x-0 ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      }`}
    >
      <div className="flex flex-col h-full">
        {/* Institutional Branding Header */}
        <div className="p-4 border-b border-slate-700/60 bg-[#071930]">
          <PIDELogo size="sm" variant="dark" />
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <div className="flex items-center justify-between px-3 mb-2">
            <span className="text-[10px] font-bold text-[#D4AF37] uppercase tracking-wider">
              {currentRole} Navigation
            </span>
            <span className={`text-[9px] font-bold px-2 py-0.5 rounded border ${roleLabels[currentRole].badgeBg} ${roleLabels[currentRole].border}`}>
              {currentRole}
            </span>
          </div>

          {filteredNavItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-[#005A36] text-white shadow-sm font-semibold border-l-4 border-[#D4AF37]'
                      : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
                  }`
                }
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* User Role Card & Status Footer */}
        <div className="p-4 border-t border-slate-800 bg-[#071930]/90 space-y-2">
          <div className="flex items-center gap-2 text-xs">
            <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            <div>
              <div className="font-bold text-white leading-tight">{user?.full_name || 'PIDE User'}</div>
              <div className="text-[10px] text-slate-400">{roleLabels[currentRole].label}</div>
            </div>
          </div>

          <div className="flex items-center justify-between pt-1 border-t border-slate-800/80">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-[11px] text-slate-300 font-medium">PEPR Core Active</span>
            </div>
            <span className="text-[10px] bg-[#D4AF37]/20 text-[#D4AF37] px-1.5 py-0.5 rounded font-mono font-bold">
              v1.0
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
};

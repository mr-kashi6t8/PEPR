import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'critical' | 'high' | 'medium' | 'low' | 'success' | 'gold' | 'navy' | 'neutral';
  size?: 'sm' | 'md';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md',
  className = '',
}) => {
  const variantStyles = {
    critical: 'bg-red-50 text-red-700 border-red-200 font-semibold',
    high: 'bg-amber-50 text-amber-800 border-amber-200 font-semibold',
    medium: 'bg-blue-50 text-blue-700 border-blue-200',
    low: 'bg-slate-100 text-slate-700 border-slate-200',
    success: 'bg-emerald-50 text-[#005A36] border-emerald-200 font-medium',
    gold: 'bg-amber-50/80 text-[#8B6E14] border-[#D4AF37]/50 font-semibold',
    navy: 'bg-[#0B2545] text-white border-transparent font-medium',
    neutral: 'bg-slate-100 text-slate-700 border-slate-200',
  };

  const sizeStyles = {
    sm: 'px-2 py-0.5 text-[10px]',
    md: 'px-2.5 py-1 text-xs',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
    >
      {children}
    </span>
  );
};

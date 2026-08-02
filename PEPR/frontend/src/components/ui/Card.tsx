import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  hoverable?: boolean;
  accentBorder?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  hoverable = false,
  accentBorder = false,
  ...props
}) => {
  return (
    <div
      className={twMerge(
        clsx(
          'bg-white rounded-xl border border-slate-200/90 shadow-xs p-5 transition-all duration-200',
          hoverable && 'hover:shadow-md hover:border-slate-300 cursor-pointer',
          accentBorder && 'border-t-4 border-t-[#005A36]',
          className
        )
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <div className={twMerge('flex items-center justify-between pb-3 border-b border-slate-100 mb-4', className)}>
    {children}
  </div>
);

export const CardTitle: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <h3 className={twMerge('text-base font-semibold text-[#0B2545] tracking-tight flex items-center gap-2', className)}>
    {children}
  </h3>
);

export const CardDescription: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <p className={twMerge('text-xs text-slate-500 font-normal mt-0.5', className)}>{children}</p>
);

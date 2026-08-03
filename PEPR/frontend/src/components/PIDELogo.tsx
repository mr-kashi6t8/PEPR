import React, { useState } from 'react';

interface PIDELogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showSubtitle?: boolean;
  variant?: 'dark' | 'light';
}

export const PIDELogo: React.FC<PIDELogoProps> = ({
  className = '',
  size = 'sm',
  showSubtitle = true,
  variant = 'dark',
}) => {
  const [imgError, setImgError] = useState(false);

  const heightMap = {
    sm: 'h-8',
    md: 'h-10',
    lg: 'h-12',
  };

  const isDark = variant === 'dark';

  return (
    <div className={`flex items-center gap-3 select-none ${className}`}>
      {/* Official PIDE Logo in a clean white container for 100% visibility against dark background */}
      {!imgError ? (
        <div className={`flex items-center justify-center bg-white p-1.5 rounded-lg shadow-sm flex-shrink-0 ${isDark ? 'border border-slate-600/40' : 'border border-slate-200'}`}>
          <img
            src="/pide-logo.png"
            alt="PIDE Official Logo"
            className={`${heightMap[size]} w-auto object-contain`}
            onError={() => setImgError(true)}
          />
        </div>
      ) : (
        /* Fallback Emblem */
        <div className={`aspect-square ${heightMap[size]} flex-shrink-0 relative`}>
          <svg viewBox="0 0 100 100" className="w-full h-full drop-shadow-sm">
            <path
              d="M 50 5 L 85 20 V 55 C 85 75 50 95 50 95 C 50 95 15 75 15 55 V 20 Z"
              fill="#005A36"
              stroke="#D4AF37"
              strokeWidth="3.5"
            />
            <path
              d="M 50 12 L 78 24 V 52 C 78 68 50 85 50 85 C 50 85 22 68 22 52 V 24 Z"
              fill="#FFFFFF"
            />
            <path d="M 32 38 L 50 48 L 68 38 L 50 28 Z" fill="#005A36" />
            <circle cx="50" cy="52" r="12" stroke="#005A36" strokeWidth="4" fill="none" />
            <line x1="58" y1="60" x2="68" y2="70" stroke="#D4AF37" strokeWidth="4" strokeLinecap="round" />
            <path d="M 35 68 C 42 75 58 75 65 68" stroke="#D4AF37" strokeWidth="3" fill="none" />
          </svg>
        </div>
      )}

      {/* Brand Text with High Contrast & Zero Readability Issues */}
      <div className="flex flex-col justify-center">
        <div className="flex items-center gap-1.5 leading-none">
          <span
            className={`font-extrabold tracking-wider text-lg font-serif ${
              isDark ? 'text-emerald-400' : 'text-[#005A36]'
            }`}
          >
            PEPR
          </span>
          <span className="h-3.5 w-[2px] bg-[#D4AF37]" />
          <span
            className={`font-bold tracking-wider text-xs uppercase ${
              isDark ? 'text-[#F59E0B]' : 'text-[#005A36]'
            }`}
          >
            PIDE
          </span>
        </div>
        {showSubtitle && (
          <span
            className={`text-[9.5px] tracking-wide font-bold font-sans uppercase mt-1 ${
              isDark ? 'text-slate-100' : 'text-slate-700'
            }`}
          >
            Pakistan Economics Problem Radar
          </span>
        )}
      </div>
    </div>
  );
};

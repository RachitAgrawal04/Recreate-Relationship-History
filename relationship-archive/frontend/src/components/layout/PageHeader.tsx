import type { ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  right?: ReactNode;
  className?: string;
}

export default function PageHeader({ title, subtitle, right, className = '' }: PageHeaderProps) {
  return (
    <header
      className={`sticky top-0 z-10 border-b backdrop-blur-sm px-4 lg:px-8 py-4 flex items-center justify-between gap-4 ${className}`}
      style={{
        backgroundColor: 'color-mix(in srgb, var(--weather-bg, #FAF7F2) 90%, transparent)',
        borderColor: 'var(--weather-border, #E4DCD0)',
      }}
    >
      <div>
        <h1
          className="font-serif text-lg lg:text-xl font-normal leading-tight text-[#1A1714]"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          {title}
        </h1>
        {subtitle && (
          <p className="text-xs text-[#9C9184] mt-0.5 font-medium tracking-wide uppercase">
            {subtitle}
          </p>
        )}
      </div>
      {right && <div>{right}</div>}
    </header>
  );
}

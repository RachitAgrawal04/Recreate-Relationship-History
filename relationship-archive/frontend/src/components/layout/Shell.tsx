import type { ReactNode } from 'react';
import Navigation from './Navigation';

interface ShellProps {
  children: ReactNode;
  mood?: string;
  weatherBg?: string;
  weatherAccent?: string;
  weatherBorder?: string;
  weatherGlow?: string;
}

export default function Shell({
  children,
  mood = 'neutral',
  weatherBg = '#FAF7F2',
  weatherAccent = '#8B7355',
  weatherBorder = '#E4DCD0',
  weatherGlow = 'transparent',
}: ShellProps) {
  return (
    <div
      data-mood={mood}
      className="min-h-screen transition-colors duration-700"
      style={{
        '--weather-bg': weatherBg,
        '--weather-accent': weatherAccent,
        '--weather-border': weatherBorder,
        '--weather-glow': weatherGlow,
        backgroundColor: weatherBg,
      } as React.CSSProperties}
    >
      <Navigation />
      {/* Skip to content */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:rounded focus:bg-white focus:text-black focus:shadow-md"
      >
        Skip to content
      </a>
      {/* Main content — offset for desktop sidebar */}
      <main
        id="main-content"
        className="lg:ml-16 pb-20 lg:pb-0 min-h-screen"
      >
        {children}
      </main>
    </div>
  );
}

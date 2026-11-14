'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

const NAV_ITEMS = [
  { href: '/', label: 'Home', icon: '◎' },
  { href: '/timeline', label: 'Timeline', icon: '◇' },
  { href: '/conversation', label: 'Chat', icon: '◈' },
  { href: '/memories', label: 'Memories', icon: '◑' },
  { href: '/chapters', label: 'Chapters', icon: '○' },
  { href: '/search', label: 'Search', icon: '⊕' },
  { href: '/analysis', label: 'Analysis', icon: '◉' },
  { href: '/about', label: 'About', icon: '◌' },
];

const PRIMARY_NAV = NAV_ITEMS.slice(0, 4);
const MORE_NAV = NAV_ITEMS.slice(4);

export default function Navigation() {
  const pathname = usePathname();

  return (
    <>
      {/* Mobile bottom nav */}
      <nav
        className="fixed bottom-0 left-0 right-0 z-20 border-t lg:hidden"
        style={{
          backgroundColor: 'var(--weather-bg, #FAF7F2)',
          borderColor: 'var(--weather-border, #E4DCD0)',
        }}
        aria-label="Main navigation"
      >
        <div className="flex h-14 items-stretch">
          {PRIMARY_NAV.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex flex-1 flex-col items-center justify-center gap-0.5 text-center transition-colors',
                  active
                    ? 'text-[color:var(--weather-accent,#8B7355)]'
                    : 'text-[#9C9184] hover:text-[#6B6259]'
                )}
                aria-current={active ? 'page' : undefined}
              >
                <span className="text-base leading-none" aria-hidden="true">
                  {item.icon}
                </span>
                <span className="text-[0.625rem] font-semibold uppercase tracking-widest leading-none">
                  {item.label}
                </span>
              </Link>
            );
          })}
          {/* More button */}
          <details className="group flex flex-1 flex-col">
            <summary className="flex flex-col items-center justify-center gap-0.5 h-14 cursor-pointer list-none text-[#9C9184] hover:text-[#6B6259]">
              <span className="text-base leading-none" aria-hidden="true">···</span>
              <span className="text-[0.625rem] font-semibold uppercase tracking-widest leading-none">More</span>
            </summary>
            <div
              className="absolute bottom-14 right-0 w-48 border rounded-tl-xl shadow-lg p-2"
              style={{
                backgroundColor: 'var(--weather-bg, #FAF7F2)',
                borderColor: 'var(--weather-border, #E4DCD0)',
              }}
            >
              {MORE_NAV.map((item) => {
                const active = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors',
                      active
                        ? 'text-[color:var(--weather-accent,#8B7355)] font-medium'
                        : 'text-[#6B6259] hover:bg-[#F3EDE4]'
                    )}
                    aria-current={active ? 'page' : undefined}
                  >
                    <span aria-hidden="true">{item.icon}</span>
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </details>
        </div>
      </nav>

      {/* Desktop sidebar */}
      <nav
        className="hidden lg:flex fixed left-0 top-0 bottom-0 z-20 flex-col border-r group/nav transition-all duration-200 w-16 hover:w-60"
        style={{
          backgroundColor: 'var(--weather-bg, #FAF7F2)',
          borderColor: 'var(--weather-border, #E4DCD0)',
        }}
        aria-label="Main navigation"
      >
        {/* Logo mark */}
        <div className="flex h-16 items-center justify-center group-hover/nav:justify-start group-hover/nav:px-5 overflow-hidden shrink-0">
          <span className="text-lg font-light tracking-widest text-[#8B7355] whitespace-nowrap">
            <span className="group-hover/nav:hidden">R×R</span>
            <span className="hidden group-hover/nav:block font-serif text-sm">Rachit × Radhika</span>
          </span>
        </div>
        <div
          className="h-px mx-4 shrink-0"
          style={{ backgroundColor: 'var(--weather-border, #E4DCD0)' }}
        />
        {/* Nav items */}
        <div className="flex flex-col gap-1 p-2 flex-1 overflow-hidden mt-2">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors whitespace-nowrap overflow-hidden',
                  active
                    ? 'text-[color:var(--weather-accent,#8B7355)] bg-[#F3EDE4]'
                    : 'text-[#6B6259] hover:bg-[#F3EDE4] hover:text-[#1A1714]'
                )}
                aria-current={active ? 'page' : undefined}
              >
                <span
                  className="text-base w-5 shrink-0 text-center leading-none"
                  aria-hidden="true"
                >
                  {item.icon}
                </span>
                <span className="text-sm font-medium opacity-0 group-hover/nav:opacity-100 transition-opacity duration-150 delay-75">
                  {item.label}
                </span>
              </Link>
            );
          })}
        </div>
      </nav>
    </>
  );
}

import Link from 'next/link';
import { ARCHIVE_STATS } from '@/lib/fixtures';
import { formatNumber } from '@/lib/utils';

function StatItem({ value, label }: { value: string; label: string }) {
  return (
    <div className="flex flex-col items-center gap-1 px-6 py-4">
      <span
        className="font-serif text-2xl lg:text-3xl font-light text-[#1A1714]"
        style={{ fontFamily: 'var(--font-serif)' }}
      >
        {value}
      </span>
      <span className="text-[0.6875rem] font-semibold uppercase tracking-widest text-[#9C9184]">
        {label}
      </span>
    </div>
  );
}

function EntryCard({ href, icon, title, desc }: {
  href: string; icon: string; title: string; desc: string;
}) {
  return (
    <Link
      href={href}
      className="group flex items-start gap-4 p-4 rounded-xl border transition-all hover:shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2"
      style={{
        borderColor: 'var(--weather-border, #E4DCD0)',
        '--tw-ring-color': '#7B8BA0',
      } as React.CSSProperties}
    >
      <span
        className="text-xl mt-0.5 shrink-0 transition-transform group-hover:scale-110"
        aria-hidden="true"
        style={{ color: 'var(--weather-accent, #8B7355)' }}
      >
        {icon}
      </span>
      <div>
        <p className="text-sm font-semibold text-[#1A1714]">{title}</p>
        <p className="text-xs text-[#9C9184] mt-0.5 leading-relaxed">{desc}</p>
      </div>
    </Link>
  );
}

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 lg:px-8">
      <div className="w-full max-w-xl mx-auto">
        {/* Title */}
        <div className="text-center mb-10 mt-16 lg:mt-0">
          <p className="text-[0.6875rem] font-semibold uppercase tracking-[0.25em] text-[#9C9184] mb-6">
            A private archive
          </p>
          <h1
            className="font-serif font-light leading-none text-[#1A1714] mb-6"
            style={{
              fontFamily: 'var(--font-serif)',
              fontSize: 'clamp(2rem, 8vw, 3.5rem)',
              letterSpacing: '-0.02em',
            }}
          >
            Rachit{' '}
            <span className="font-light" style={{ color: 'var(--weather-accent, #8B7355)' }}>
              ×
            </span>{' '}
            Radhika
          </h1>

          <div
            className="w-16 h-px mx-auto mb-6"
            style={{ backgroundColor: 'var(--weather-border, #E4DCD0)' }}
          />

          <p
            className="font-serif italic text-base lg:text-lg text-[#6B6259] leading-relaxed"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            A record of us,{' '}
            <span className="not-italic text-[#9C9184] text-sm">
              May – November 2026
            </span>
          </p>
        </div>

        {/* Stats */}
        <div
          className="flex justify-center divide-x rounded-xl border mb-8"
          style={{
            borderColor: 'var(--weather-border, #E4DCD0)',
            backgroundColor: 'rgba(255,255,255,0.4)',
          }}
        >
          <StatItem value={formatNumber(ARCHIVE_STATS.total_messages)} label="messages" />
          <StatItem value={String(ARCHIVE_STATS.total_days)} label="days" />
          <StatItem value={formatNumber(ARCHIVE_STATS.media_items)} label="moments" />
        </div>

        {/* Primary CTA */}
        <div className="flex gap-3 mb-8 justify-center">
          <Link
            href="/conversation"
            className="flex-1 max-w-[200px] text-center py-3 px-6 rounded-xl text-sm font-semibold transition-all hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2"
            style={{
              backgroundColor: 'var(--weather-accent, #8B7355)',
              color: '#FAF7F2',
              '--tw-ring-color': '#7B8BA0',
            } as React.CSSProperties}
          >
            Begin reading →
          </Link>
          <Link
            href="/timeline"
            className="flex-1 max-w-[200px] text-center py-3 px-6 rounded-xl text-sm font-semibold border transition-all hover:shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2"
            style={{
              borderColor: 'var(--weather-border, #E4DCD0)',
              color: '#6B6259',
              '--tw-ring-color': '#7B8BA0',
            } as React.CSSProperties}
          >
            View timeline
          </Link>
        </div>

        {/* Quick nav */}
        <div className="grid grid-cols-2 gap-3 mb-16">
          <EntryCard href="/chapters" icon="○" title="Chapters" desc="Four story arcs across six months" />
          <EntryCard href="/memories" icon="◑" title="Memories" desc="910 shared photos, videos, and moments" />
          <EntryCard href="/analysis" icon="◉" title="Analysis" desc="An outside view of the archive" />
          <EntryCard href="/search" icon="⊕" title="Search" desc="Find any message instantly" />
        </div>

        <p className="text-center text-[0.6875rem] text-[#9C9184] pb-8 opacity-60">
          Entirely private. Nothing published or shared.
        </p>
      </div>
    </div>
  );
}

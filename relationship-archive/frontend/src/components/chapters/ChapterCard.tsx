import type { Chapter } from '@/lib/types';
import { WEATHER_TOKENS } from '@/lib/emotional-weather';
import { formatNumber } from '@/lib/utils';
import Link from 'next/link';

interface ChapterCardProps {
  chapter: Chapter;
}

export default function ChapterCard({ chapter }: ChapterCardProps) {
  const tokens = WEATHER_TOKENS[chapter.mood];

  return (
    <Link
      href={`/chapters/${chapter.id}`}
      className="block group focus:outline-none focus:ring-2 focus:ring-offset-2 rounded-2xl"
      style={{ '--tw-ring-color': '#7B8BA0' } as React.CSSProperties}
      aria-label={`Chapter ${chapter.number}: ${chapter.title}`}
    >
      <article
        className="rounded-2xl border overflow-hidden transition-all duration-300 group-hover:shadow-md group-focus:shadow-md"
        style={{
          backgroundColor: tokens.bg,
          borderColor: tokens.border,
        }}
      >
        {/* Cover area */}
        <div
          className="h-36 lg:h-44 flex items-end px-5 pb-4 relative overflow-hidden"
          style={{ backgroundColor: chapter.cover_color }}
        >
          {/* Chapter number — large background numeral */}
          <span
            className="absolute top-2 right-4 font-serif text-[6rem] lg:text-[8rem] leading-none select-none pointer-events-none"
            style={{
              color: tokens.border,
              fontFamily: 'var(--font-serif)',
              opacity: 0.5,
            }}
            aria-hidden="true"
          >
            {String(chapter.number).padStart(2, '0')}
          </span>

          {/* Mood indicator */}
          <span
            className="text-[0.6rem] font-bold uppercase tracking-widest px-2 py-1 rounded-full"
            style={{
              backgroundColor: 'rgba(255,255,255,0.7)',
              color: tokens.accent,
            }}
          >
            {chapter.mood}
          </span>
        </div>

        {/* Content */}
        <div className="p-5">
          <p
            className="text-[0.6875rem] font-semibold uppercase tracking-widest mb-1"
            style={{ color: tokens.accent }}
          >
            {chapter.date_range_display}
          </p>
          <h2
            className="font-serif text-xl font-normal text-[#1A1714] leading-tight mb-1"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            {chapter.title}
          </h2>
          <p className="text-sm text-[#9C9184] mb-3 italic">{chapter.subtitle}</p>
          <p className="text-sm text-[#6B6259] leading-relaxed line-clamp-3">
            {chapter.excerpt}
          </p>

          <div className="flex items-center justify-between mt-4 pt-4 border-t"
            style={{ borderColor: tokens.border }}>
            <span className="text-xs text-[#9C9184]">
              {formatNumber(chapter.message_count)} messages
            </span>
            <div className="flex gap-1">
              {chapter.platforms.map((p) => (
                <span
                  key={p}
                  className="text-[0.55rem] font-bold uppercase tracking-wider"
                  style={{ color: p === 'whatsapp' ? '#6B8F71' : '#8B6B8F' }}
                >
                  {p === 'whatsapp' ? 'WA' : 'IG'}
                </span>
              ))}
            </div>
          </div>
        </div>
      </article>
    </Link>
  );
}

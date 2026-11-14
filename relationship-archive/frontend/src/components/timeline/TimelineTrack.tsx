import type { TimelineMonth } from '@/lib/types';
import { WEATHER_TOKENS } from '@/lib/emotional-weather';
import { formatNumber } from '@/lib/utils';
import Link from 'next/link';

function DensityBar({ count, max }: { count: number; max: number }) {
  const pct = Math.round((count / max) * 100);
  return (
    <div
      className="h-1 rounded-full overflow-hidden"
      style={{ backgroundColor: 'var(--weather-border, #E4DCD0)' }}
      aria-label={`${count} messages`}
    >
      <div
        className="h-full rounded-full transition-all"
        style={{
          width: `${pct}%`,
          backgroundColor: 'var(--weather-accent, #8B7355)',
          opacity: 0.6,
        }}
      />
    </div>
  );
}

interface TimelineTrackProps {
  months: TimelineMonth[];
}

export default function TimelineTrack({ months }: TimelineTrackProps) {
  const maxMessages = Math.max(...months.map((m) => m.message_count));

  return (
    <div className="relative px-4 lg:px-8 max-w-2xl mx-auto py-8">
      {/* Spine */}
      <div
        className="absolute left-8 lg:left-12 top-8 bottom-8 w-px"
        style={{ backgroundColor: 'var(--weather-border, #E4DCD0)' }}
        aria-hidden="true"
      />

      <div className="space-y-10">
        {months.map((month) => {
          const tokens = WEATHER_TOKENS[month.dominant_mood];
          return (
            <div key={month.month_key} className="relative pl-8 lg:pl-12">
              {/* Month dot */}
              <div
                className="absolute left-[1.875rem] lg:left-[2.875rem] top-1 w-2.5 h-2.5 rounded-full border-2 ring-4"
                style={{
                  backgroundColor: tokens.accent,
                  borderColor: tokens.bg,
                  boxShadow: `0 0 0 3px ${tokens.bg}`,
                }}
                aria-hidden="true"
              />

              {/* Month card */}
              <div
                className="ml-4 rounded-xl p-4 border transition-all duration-500"
                style={{
                  backgroundColor: tokens.bg,
                  borderColor: tokens.border,
                }}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h2
                    className="font-serif text-lg font-normal leading-tight text-[#1A1714]"
                    style={{ fontFamily: 'var(--font-serif)' }}
                  >
                    {month.month_display}
                  </h2>
                  <span className="text-xs text-[#9C9184] font-mono whitespace-nowrap mt-0.5">
                    {formatNumber(month.message_count)} msgs
                  </span>
                </div>

                {/* Platform tags */}
                <div className="flex gap-1.5 mb-3">
                  {month.platforms.map((p) => (
                    <span
                      key={p}
                      className="text-[0.6rem] font-bold uppercase tracking-widest px-1.5 py-0.5 rounded"
                      style={{
                        color: p === 'whatsapp' ? '#6B8F71' : '#8B6B8F',
                        backgroundColor: p === 'whatsapp'
                          ? 'rgba(107,143,113,0.1)'
                          : 'rgba(139,107,143,0.1)',
                      }}
                    >
                      {p === 'whatsapp' ? 'WhatsApp' : 'Instagram'}
                    </span>
                  ))}
                </div>

                {/* Density bar */}
                <DensityBar count={month.message_count} max={maxMessages} />

                {/* Events */}
                {month.events.length > 0 && (
                  <div className="mt-3 space-y-1.5">
                    {month.events.map((ev) => (
                      <div key={ev.id} className="flex items-center gap-2">
                        <span
                          className="w-1 h-1 rounded-full shrink-0"
                          style={{ backgroundColor: tokens.accent }}
                          aria-hidden="true"
                        />
                        <span className="text-xs text-[#6B6259]">
                          <span className="text-[#9C9184] font-mono mr-1.5">
                            {ev.date.substring(8)}
                          </span>
                          {ev.label}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Mood badge */}
                <div className="mt-3 flex justify-end">
                  <span
                    className="text-[0.6rem] uppercase tracking-widest font-semibold"
                    style={{ color: tokens.accent }}
                  >
                    {month.dominant_mood}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

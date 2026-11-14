'use client';

import { useState } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import MediaGrid from '@/components/media/MediaGrid';
import { FIXTURE_MEDIA } from '@/lib/fixtures';
import type { MediaItem } from '@/lib/types';

const KIND_FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'photo', label: 'Photos' },
  { key: 'video', label: 'Videos' },
  { key: 'audio', label: 'Audio' },
];

export default function MemoriesPage() {
  const [activeKind, setActiveKind] = useState('all');

  const filtered: MediaItem[] =
    activeKind === 'all'
      ? FIXTURE_MEDIA
      : FIXTURE_MEDIA.filter((m) => m.kind === activeKind);

  return (
    <>
      <PageHeader
        title="Memories"
        subtitle={`${FIXTURE_MEDIA.length} of 910 shown (synthetic preview)`}
      />

      {/* Filters */}
      <div
        className="flex gap-2 px-4 lg:px-8 py-3 overflow-x-auto scrollbar-none border-b"
        style={{ borderColor: 'var(--weather-border, #E4DCD0)' }}
      >
        {KIND_FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => setActiveKind(f.key)}
            className="shrink-0 text-xs font-semibold px-3 py-1.5 rounded-full border transition-all focus:outline-none focus:ring-2 focus:ring-offset-1"
            style={{
              backgroundColor:
                activeKind === f.key
                  ? 'var(--weather-accent, #8B7355)'
                  : 'transparent',
              color: activeKind === f.key ? '#FAF7F2' : '#6B6259',
              borderColor:
                activeKind === f.key
                  ? 'var(--weather-accent, #8B7355)'
                  : 'var(--weather-border, #E4DCD0)',
              '--tw-ring-color': '#7B8BA0',
            } as React.CSSProperties}
            aria-pressed={activeKind === f.key}
          >
            {f.label}
          </button>
        ))}

        {/* Sensitive note */}
        <span className="ml-auto shrink-0 self-center text-[0.6875rem] text-[#9C9184]">
          🔒 = tap to reveal
        </span>
      </div>

      {/* Grid */}
      <div className="py-4">
        <MediaGrid items={filtered} />
      </div>
    </>
  );
}

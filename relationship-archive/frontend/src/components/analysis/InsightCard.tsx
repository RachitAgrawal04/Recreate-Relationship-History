'use client';

import { useState } from 'react';
import type { InsightCard } from '@/lib/types';

const CATEGORY_ICONS: Record<string, string> = {
  communication: '◎',
  language: '◈',
  emotion: '◇',
  temporal: '○',
  pattern: '◑',
};

interface InsightCardProps {
  insight: InsightCard;
}

export default function InsightCardComponent({ insight }: InsightCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <article
      className="rounded-xl border overflow-hidden transition-all duration-300"
      style={{
        backgroundColor: '#EEF0F3',
        borderColor: '#D4DAE3',
      }}
    >
      {/* Header */}
      <div className="px-5 pt-5 pb-4">
        <div className="flex items-start gap-3">
          <span
            className="text-xl mt-0.5 shrink-0"
            aria-hidden="true"
            style={{ color: '#7B8BA0' }}
          >
            {insight.icon}
          </span>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span
                className="text-[0.6rem] font-bold uppercase tracking-widest"
                style={{ color: '#7B8BA0' }}
              >
                AI · {insight.category}
              </span>
            </div>
            <h3
              className="font-serif text-base font-normal text-[#1A1714] leading-tight"
              style={{ fontFamily: 'var(--font-serif)' }}
            >
              {insight.title}
            </h3>
          </div>
        </div>
      </div>

      {/* Content */}
      <div
        className="px-5 pb-4 border-t"
        style={{ borderColor: '#D4DAE3' }}
      >
        <p className="text-sm text-[#4A5568] leading-relaxed mt-4 italic">
          {insight.content}
        </p>

        {/* Expanded content */}
        {expanded && insight.expanded_content && (
          <div
            className="mt-3 pt-3 border-t"
            style={{ borderColor: '#D4DAE3' }}
          >
            <p className="text-sm text-[#4A5568] leading-relaxed">
              {insight.expanded_content}
            </p>
          </div>
        )}

        {/* Toggle */}
        {insight.expanded_content && (
          <button
            onClick={() => setExpanded((v) => !v)}
            className="mt-3 text-xs font-medium transition-colors hover:opacity-80 focus:outline-none focus:underline"
            style={{ color: '#7B8BA0' }}
            aria-expanded={expanded}
          >
            {expanded ? '↑ Less' : '↓ Read more'}
          </button>
        )}
      </div>
    </article>
  );
}

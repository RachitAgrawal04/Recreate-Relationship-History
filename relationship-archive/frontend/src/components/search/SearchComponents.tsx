'use client';

import { useState, useRef, useEffect } from 'react';
import type { Message } from '@/lib/types';
import { FIXTURE_MESSAGES } from '@/lib/fixtures';
import ChatBubble from '@/components/chat/ChatBubble';
import { formatShortDate } from '@/lib/utils';

interface SearchResult {
  message: Message;
  score: number;
}

function highlightText(text: string, query: string): React.ReactNode {
  if (!query.trim()) return text;
  const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
  const parts = text.split(regex);
  return parts.map((part, i) =>
    regex.test(part) ? (
      <mark
        key={i}
        style={{ backgroundColor: 'rgba(196,146,61,0.25)', borderRadius: '2px' }}
      >
        {part}
      </mark>
    ) : part
  );
}

function searchMessages(query: string): SearchResult[] {
  if (!query.trim()) return [];
  const q = query.toLowerCase();
  return FIXTURE_MESSAGES
    .filter((m) => m.text_display.toLowerCase().includes(q))
    .map((m) => ({ message: m, score: 1 }))
    .slice(0, 20);
}

const FILTER_OPTIONS = [
  { key: 'all', label: 'All' },
  { key: 'whatsapp', label: 'WhatsApp' },
  { key: 'instagram', label: 'Instagram' },
  { key: 'person-a', label: 'Rachit' },
  { key: 'person-b', label: 'Radhika' },
  { key: 'photo', label: 'Photos' },
  { key: 'video', label: 'Videos' },
];

interface SearchBarProps {
  onResults: (results: SearchResult[], query: string) => void;
}

export function SearchBar({ onResults }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState('all');
  const inputRef = useRef<HTMLInputElement>(null);

  // "/" shortcut
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === '/' && document.activeElement !== inputRef.current) {
        e.preventDefault();
        inputRef.current?.focus();
      }
      if (e.key === 'Escape') {
        setQuery('');
        onResults([], '');
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onResults]);

  useEffect(() => {
    const timer = setTimeout(() => {
      onResults(searchMessages(query), query);
    }, 200);
    return () => clearTimeout(timer);
  }, [query, onResults]);

  return (
    <div className="px-4 lg:px-8 pt-6 pb-4">
      {/* Input */}
      <div className="relative">
        <span
          className="absolute left-4 top-1/2 -translate-y-1/2 text-[#9C9184] text-sm"
          aria-hidden="true"
        >
          ⊕
        </span>
        <input
          ref={inputRef}
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder='Search messages… (press "/" to focus)'
          className="w-full pl-10 pr-10 py-3 rounded-xl border text-sm bg-transparent focus:outline-none focus:ring-2 transition-shadow"
          style={{
            borderColor: 'var(--weather-border, #E4DCD0)',
            color: '#1A1714',
            '--tw-ring-color': '#7B8BA0',
          } as React.CSSProperties}
          aria-label="Search messages"
        />
        {query && (
          <button
            className="absolute right-3 top-1/2 -translate-y-1/2 text-[#9C9184] hover:text-[#1A1714] transition-colors text-lg"
            onClick={() => { setQuery(''); onResults([], ''); }}
            aria-label="Clear search"
          >
            ✕
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="flex gap-2 mt-3 overflow-x-auto pb-1 scrollbar-none">
        {FILTER_OPTIONS.map((f) => (
          <button
            key={f.key}
            onClick={() => setActiveFilter(f.key)}
            className="shrink-0 text-xs font-semibold px-3 py-1.5 rounded-full border transition-all"
            style={{
              backgroundColor: activeFilter === f.key
                ? 'var(--weather-accent, #8B7355)'
                : 'transparent',
              color: activeFilter === f.key ? '#FAF7F2' : '#6B6259',
              borderColor: activeFilter === f.key
                ? 'var(--weather-accent, #8B7355)'
                : 'var(--weather-border, #E4DCD0)',
            }}
            aria-pressed={activeFilter === f.key}
          >
            {f.label}
          </button>
        ))}
      </div>
    </div>
  );
}

interface SearchResultsProps {
  results: SearchResult[];
  query: string;
}

export function SearchResults({ results, query }: SearchResultsProps) {
  if (!query.trim()) {
    return (
      <div className="px-4 lg:px-8 py-16 text-center">
        <p className="text-[#9C9184] text-sm">
          Type to search across {(38558).toLocaleString('en-IN')} messages
        </p>
        <p className="text-xs text-[#9C9184] mt-2 opacity-60">
          Press <kbd className="px-1.5 py-0.5 rounded border text-[0.65rem]" style={{ borderColor: '#E4DCD0' }}>/</kbd> to focus
        </p>
      </div>
    );
  }

  if (!results.length) {
    return (
      <div className="px-4 lg:px-8 py-16 text-center">
        <p className="text-[#9C9184] text-sm">No messages found for &ldquo;{query}&rdquo;</p>
      </div>
    );
  }

  return (
    <div className="px-4 lg:px-8">
      <p className="text-xs text-[#9C9184] mb-4 font-medium">
        {results.length} result{results.length !== 1 ? 's' : ''} for &ldquo;{query}&rdquo;
      </p>
      <div className="space-y-6">
        {results.map(({ message }) => (
          <div key={message.event_id}>
            {/* Context line */}
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-xs text-[#9C9184]">
                {formatShortDate(message.timestamp_parsed)}
              </span>
              <span
                className="text-[0.6rem] font-bold uppercase tracking-wider"
                style={{ color: message.platform === 'whatsapp' ? '#6B8F71' : '#8B6B8F' }}
              >
                {message.platform === 'whatsapp' ? 'WA' : 'IG'}
              </span>
              <span className="text-xs text-[#6B6259]">
                {message.sender_display}
              </span>
            </div>

            {/* Message preview with highlight */}
            <div
              className="text-sm text-[#1A1714] leading-relaxed px-3 py-2.5 rounded-lg border"
              style={{
                backgroundColor: 'var(--weather-bg, #FAF7F2)',
                borderColor: 'var(--weather-border, #E4DCD0)',
              }}
            >
              {highlightText(message.text_display, query)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

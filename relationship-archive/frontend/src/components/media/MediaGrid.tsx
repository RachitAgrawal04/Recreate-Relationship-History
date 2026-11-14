'use client';

import { useState } from 'react';
import type { MediaItem } from '@/lib/types';
import { formatShortDate } from '@/lib/utils';
import { useMediaReveal } from '@/hooks/useMediaReveal';

interface MediaGridItemProps {
  item: MediaItem;
  onClick: (item: MediaItem) => void;
}

function MediaGridItem({ item, onClick }: MediaGridItemProps) {
  const { revealed, reveal } = useMediaReveal(item.is_sensitive);

  const bgColors = {
    photo: '#E8DED2',
    video: '#DDE4DB',
    audio: '#E8E4D8',
    sticker: '#F3EDE4',
  };

  return (
    <div className="relative aspect-square rounded-lg overflow-hidden group">
      {/* Thumbnail placeholder */}
      <button
        className="w-full h-full flex items-center justify-center transition-transform duration-200 group-hover:scale-105 focus:outline-none focus:ring-2 focus:ring-offset-1"
        style={{
          backgroundColor: bgColors[item.kind],
          '--tw-ring-color': '#7B8BA0',
        } as React.CSSProperties}
        onClick={() => revealed ? onClick(item) : reveal()}
        aria-label={item.is_sensitive && !revealed ? 'Reveal sensitive media' : `Open ${item.kind}`}
      >
        {/* Kind icon */}
        <span className="text-2xl" aria-hidden="true">
          {item.kind === 'photo' ? '🖼' :
           item.kind === 'video' ? '▶' :
           item.kind === 'audio' ? '🎵' : '✦'}
        </span>

        {/* Sensitive blur overlay */}
        {item.is_sensitive && !revealed && (
          <div
            className="absolute inset-0 flex flex-col items-center justify-center gap-1"
            style={{ backdropFilter: 'blur(12px)', backgroundColor: 'rgba(212,207,200,0.5)' }}
          >
            <span className="text-lg">🔒</span>
            <span className="text-[0.6rem] font-semibold text-[#6B6259] uppercase tracking-widest">
              Tap to reveal
            </span>
          </div>
        )}
      </button>

      {/* Platform badge */}
      <span
        className="absolute top-1.5 left-1.5 text-[0.5rem] font-bold uppercase tracking-wider px-1 py-0.5 rounded"
        style={{
          backgroundColor: 'rgba(250,247,242,0.85)',
          color: item.platform === 'whatsapp' ? '#6B8F71' : '#8B6B8F',
        }}
      >
        {item.platform === 'whatsapp' ? 'WA' : 'IG'}
      </span>

      {/* Video duration badge */}
      {item.kind === 'video' && item.duration_seconds && (
        <span
          className="absolute bottom-1.5 right-1.5 text-[0.6rem] font-mono px-1 py-0.5 rounded"
          style={{ backgroundColor: 'rgba(26,23,20,0.6)', color: '#FAF7F2' }}
        >
          {Math.floor(item.duration_seconds / 60)}:{String(item.duration_seconds % 60).padStart(2, '0')}
        </span>
      )}
    </div>
  );
}

interface MediaGridProps {
  items: MediaItem[];
}

export default function MediaGrid({ items }: MediaGridProps) {
  const [viewerItem, setViewerItem] = useState<MediaItem | null>(null);
  const [viewerIndex, setViewerIndex] = useState(0);

  function openViewer(item: MediaItem) {
    const idx = items.findIndex((i) => i.event_id === item.event_id);
    setViewerIndex(idx);
    setViewerItem(item);
  }

  function closeViewer() {
    setViewerItem(null);
  }

  function prevItem() {
    const idx = Math.max(0, viewerIndex - 1);
    setViewerIndex(idx);
    setViewerItem(items[idx]);
  }

  function nextItem() {
    const idx = Math.min(items.length - 1, viewerIndex + 1);
    setViewerIndex(idx);
    setViewerItem(items[idx]);
  }

  if (!items.length) {
    return (
      <div className="flex items-center justify-center py-20 text-[#9C9184] text-sm">
        No media found.
      </div>
    );
  }

  return (
    <>
      {/* Grid */}
      <div className="grid grid-cols-3 lg:grid-cols-5 gap-1.5 px-4 lg:px-8">
        {items.map((item) => (
          <MediaGridItem key={item.event_id} item={item} onClick={openViewer} />
        ))}
      </div>

      {/* Lightbox viewer */}
      {viewerItem && (
        <div
          className="fixed inset-0 z-40 flex items-center justify-center"
          style={{ backgroundColor: 'rgba(28,23,20,0.95)' }}
          role="dialog"
          aria-modal="true"
          aria-label="Media viewer"
          onClick={closeViewer}
        >
          <div
            className="relative max-w-lg w-full mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close */}
            <button
              className="absolute -top-12 right-0 text-white opacity-70 hover:opacity-100 text-2xl w-11 h-11 flex items-center justify-center rounded-full transition-opacity"
              onClick={closeViewer}
              aria-label="Close media viewer"
            >
              ✕
            </button>

            {/* Content */}
            <div
              className="rounded-xl overflow-hidden aspect-square flex items-center justify-center"
              style={{ backgroundColor: '#2C2825' }}
            >
              <span className="text-5xl" aria-hidden="true">
                {viewerItem.kind === 'photo' ? '🖼' :
                 viewerItem.kind === 'video' ? '▶' :
                 viewerItem.kind === 'audio' ? '🎵' : '✦'}
              </span>
            </div>

            {/* Caption */}
            <div className="mt-3 text-center">
              <p className="text-xs text-[#9C9184]">
                {viewerItem.sender_id === 'person-a' ? 'Rachit' : 'Radhika'}
                {' · '}
                {formatShortDate(viewerItem.timestamp_parsed)}
                {' · '}
                <span style={{ color: viewerItem.platform === 'whatsapp' ? '#6B8F71' : '#8B6B8F' }}>
                  {viewerItem.platform === 'whatsapp' ? 'WhatsApp' : 'Instagram'}
                </span>
              </p>
              {viewerItem.caption && (
                <p className="text-sm text-[#FAF7F2] mt-1 opacity-80">{viewerItem.caption}</p>
              )}
            </div>

            {/* Prev / Next */}
            <div className="flex justify-between mt-4">
              <button
                className="text-white opacity-50 hover:opacity-100 disabled:opacity-20 transition-opacity text-lg px-3 py-1 rounded"
                onClick={prevItem}
                disabled={viewerIndex === 0}
                aria-label="Previous"
              >
                ← Prev
              </button>
              <span className="text-xs text-[#9C9184] self-center">
                {viewerIndex + 1} / {items.length}
              </span>
              <button
                className="text-white opacity-50 hover:opacity-100 disabled:opacity-20 transition-opacity text-lg px-3 py-1 rounded"
                onClick={nextItem}
                disabled={viewerIndex === items.length - 1}
                aria-label="Next"
              >
                Next →
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

'use client';

import { useState } from 'react';
import type { Message } from '@/lib/types';
import { formatTimestamp, containsDevanagari, cn } from '@/lib/utils';
import { useMediaReveal } from '@/hooks/useMediaReveal';

interface ChatBubbleProps {
  message: Message;
  isGrouped?: boolean;
  isFirstInGroup?: boolean;
  isLastInGroup?: boolean;
  showPlatformBadge?: boolean;
}

function PlatformBadge({ platform }: { platform: 'whatsapp' | 'instagram' }) {
  return (
    <span
      className="text-[0.55rem] font-bold uppercase tracking-wider leading-none ml-1"
      style={{
        color: platform === 'whatsapp' ? '#6B8F71' : '#8B6B8F',
      }}
      aria-label={platform === 'whatsapp' ? 'WhatsApp' : 'Instagram'}
    >
      {platform === 'whatsapp' ? 'WA' : 'IG'}
    </span>
  );
}

function ReactionPills({ reactions }: { reactions: Message['reactions'] }) {
  if (!reactions.length) return null;
  return (
    <div className="flex gap-1 mt-1">
      {reactions.map((r, i) => (
        <span
          key={i}
          className="inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full text-xs border shadow-sm"
          style={{
            backgroundColor: '#FAF7F2',
            borderColor: '#E4DCD0',
          }}
          title={r.reactors.join(', ')}
        >
          {r.emoji}
          {r.count > 1 && (
            <span className="text-[0.65rem] text-[#9C9184]">{r.count}</span>
          )}
        </span>
      ))}
    </div>
  );
}

function SensitiveReveal({ children, isRevealed, onReveal }: {
  children: React.ReactNode;
  isRevealed: boolean;
  onReveal: () => void;
}) {
  return (
    <div className="relative">
      <div
        className={cn(
          'transition-all duration-300',
          !isRevealed && 'blur-lg select-none pointer-events-none'
        )}
        style={{ filter: isRevealed ? 'none' : 'blur(16px)' }}
        aria-hidden={!isRevealed}
      >
        {children}
      </div>
      {!isRevealed && (
        <button
          onClick={onReveal}
          onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onReveal()}
          className="absolute inset-0 flex items-center justify-center cursor-pointer focus:outline-none focus:ring-2 focus:ring-offset-1 rounded-lg"
          style={{ '--tw-ring-color': '#7B8BA0' } as React.CSSProperties}
          aria-label="Reveal sensitive content"
        >
          <span
            className="text-xs font-medium px-3 py-1.5 rounded-full border backdrop-blur-sm"
            style={{
              backgroundColor: 'rgba(250,247,242,0.9)',
              borderColor: '#C4B8A8',
              color: '#6B6259',
            }}
          >
            Tap to reveal
          </span>
        </button>
      )}
    </div>
  );
}

function MediaContent({ message }: { message: Message }) {
  const { revealed, reveal } = useMediaReveal(message.is_sensitive ?? false);
  const att = message.attachments[0];
  if (!att) return null;

  const inner = (
    <div className="mt-1.5 rounded-lg overflow-hidden max-w-[240px]">
      {att.media_type === 'photo' && (
        <div
          className="w-full h-40 rounded-lg flex items-center justify-center text-sm"
          style={{ backgroundColor: '#E8DED2' }}
          aria-label="Photo attachment"
        >
          <span className="text-2xl">🖼</span>
        </div>
      )}
      {att.media_type === 'video' && (
        <div
          className="w-full h-40 rounded-lg flex flex-col items-center justify-center gap-2"
          style={{ backgroundColor: '#DDE4DB' }}
          aria-label="Video attachment"
        >
          <span className="text-3xl">▶</span>
          <span className="text-xs text-[#6B6259]">Video</span>
        </div>
      )}
      {att.media_type === 'audio' && (
        <div
          className="flex items-center gap-3 px-4 py-3 rounded-lg min-w-[180px]"
          style={{ backgroundColor: 'rgba(0,0,0,0.04)' }}
          aria-label="Audio message"
        >
          <span className="text-lg">🎵</span>
          <div className="flex gap-0.5 items-end h-5">
            {Array.from({ length: 18 }).map((_, i) => (
              <div
                key={i}
                className="w-0.5 rounded-full"
                style={{
                  height: `${25 + Math.sin(i * 0.8) * 60}%`,
                  backgroundColor: '#8B7355',
                  opacity: 0.6,
                }}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );

  if (message.is_sensitive) {
    return <SensitiveReveal isRevealed={revealed} onReveal={reveal}>{inner}</SensitiveReveal>;
  }
  return inner;
}

function CallMessage({ message }: { message: Message }) {
  const dur = message.call_duration_seconds;
  const mins = dur ? Math.floor(dur / 60) : 0;
  return (
    <div className="flex items-center gap-2 text-xs text-[#9C9184] py-2">
      <span>📞</span>
      <span className="font-medium">{message.sender_display} started a call</span>
      {mins > 0 && <span>· {mins} min</span>}
    </div>
  );
}

export default function ChatBubble({
  message,
  isGrouped = false,
  isFirstInGroup = true,
  isLastInGroup = true,
  showPlatformBadge = true,
}: ChatBubbleProps) {
  const isA = message.sender_id === 'person-a';

  // System message (call)
  if (message.kind === 'call') {
    return (
      <div className="flex justify-center my-3">
        <div
          className="rounded-full px-4 py-1.5 border"
          style={{
            backgroundColor: '#F3EDE4',
            borderColor: '#E4DCD0',
          }}
        >
          <CallMessage message={message} />
        </div>
      </div>
    );
  }

  const hasText = message.text_display.trim().length > 0;
  const hasMedia = message.attachments.length > 0;
  const isDevanagari = hasText && containsDevanagari(message.text_display);

  // Border radius: tail corner is 4px, rest are 12px
  const radiusA = isFirstInGroup
    ? '4px 12px 12px 12px'
    : '12px 12px 12px 12px';
  const radiusB = isFirstInGroup
    ? '12px 4px 12px 12px'
    : '12px 12px 12px 12px';

  const bubbleBg = isA ? '#E8DED2' : '#DDE4DB';
  const bubbleText = isA ? '#2C2419' : '#1A2419';
  const marginTop = isGrouped && !isFirstInGroup ? '2px' : '12px';

  return (
    <div
      className={cn('flex flex-col', isA ? 'items-start' : 'items-end')}
      style={{ marginTop }}
    >
      <div className="max-w-[85%] lg:max-w-[65%]">
        {/* Bubble */}
        <div
          className="relative px-3 py-2"
          style={{
            backgroundColor: bubbleBg,
            borderRadius: isA ? radiusA : radiusB,
          }}
        >
          {/* Media */}
          {hasMedia && <MediaContent message={message} />}

          {/* Text */}
          {hasText && (
            <p
              className="text-[0.9375rem] leading-relaxed break-words"
              style={{
                color: bubbleText,
                fontFamily: isDevanagari
                  ? 'var(--font-devanagari), var(--font-sans)'
                  : 'var(--font-sans)',
                lineHeight: isDevanagari ? '1.7' : '1.5',
              }}
            >
              {message.text_display}
            </p>
          )}

          {/* Timestamp + platform */}
          {isLastInGroup && (
            <div
              className={cn(
                'flex items-center gap-1 mt-1',
                isA ? 'justify-start' : 'justify-end'
              )}
            >
              <span
                className="text-[0.6875rem] leading-none"
                style={{
                  color: '#9C9184',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                {formatTimestamp(message.timestamp_parsed)}
              </span>
              {showPlatformBadge && (
                <PlatformBadge platform={message.platform} />
              )}
            </div>
          )}
        </div>

        {/* Reactions */}
        <div className={isA ? 'ml-1' : 'mr-1'}>
          <ReactionPills reactions={message.reactions} />
        </div>
      </div>

      {/* AI Annotation */}
      {message.ai_annotation && (
        <div
          className="mt-2 max-w-[90%] lg:max-w-[75%] rounded-r-lg border-l-[3px] px-4 py-2.5"
          style={{
            backgroundColor: '#EEF0F3',
            borderColor: '#7B8BA0',
          }}
          aria-label="AI analysis annotation"
        >
          <span
            className="text-[0.6rem] font-bold uppercase tracking-widest block mb-1"
            style={{ color: '#7B8BA0' }}
          >
            AI
          </span>
          <p className="text-[0.8125rem] italic leading-relaxed text-[#4A5568]">
            {message.ai_annotation}
          </p>
        </div>
      )}

      {/* Human Note */}
      {message.human_note && (
        <div
          className="mt-2 max-w-[90%] lg:max-w-[75%] rounded-r-lg border-l-[3px] px-4 py-2.5"
          style={{
            backgroundColor: '#F5EFE8',
            borderColor: '#A07B5A',
          }}
          aria-label="Personal note"
        >
          <span
            className="text-[0.6rem] font-bold uppercase tracking-widest block mb-1"
            style={{ color: '#A07B5A' }}
          >
            Note
          </span>
          <p className="text-[0.8125rem] leading-relaxed text-[#5A3D22]">
            {message.human_note}
          </p>
        </div>
      )}
    </div>
  );
}

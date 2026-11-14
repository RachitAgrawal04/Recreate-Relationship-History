import type { Message, EmotionalWeatherMood } from './types';

export function formatTimestamp(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleTimeString('en-IN', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

export function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString('en-IN', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

export function formatShortDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

export function formatMonth(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString('en-IN', {
    month: 'long',
    year: 'numeric',
  });
}

export function formatCallDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  if (m === 0) return `${s}s`;
  return `${m} min${s > 0 ? ` ${s}s` : ''}`;
}

export function getDateKey(isoString: string): string {
  return isoString.substring(0, 10);
}

export function isSameDay(a: string, b: string): boolean {
  return getDateKey(a) === getDateKey(b);
}

/** Group consecutive messages from same sender within 2 minutes */
export function isGroupedWith(prev: Message, curr: Message): boolean {
  if (prev.sender_id !== curr.sender_id) return false;
  if (prev.platform !== curr.platform) return false;
  const prevTime = new Date(prev.timestamp_parsed).getTime();
  const currTime = new Date(curr.timestamp_parsed).getTime();
  return currTime - prevTime < 2 * 60 * 1000; // 2 minutes
}

export function formatNumber(n: number): string {
  return n.toLocaleString('en-IN');
}

export function containsDevanagari(text: string): boolean {
  return /[\u0900-\u097F]/.test(text);
}

/** Clamp a string to n characters with ellipsis */
export function truncate(str: string, n: number): string {
  return str.length > n ? str.substring(0, n).trim() + '…' : str;
}

export function cn(...classes: (string | undefined | false | null)[]): string {
  return classes.filter(Boolean).join(' ');
}

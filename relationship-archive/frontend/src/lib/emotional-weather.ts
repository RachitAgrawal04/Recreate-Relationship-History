import type { EmotionalWeatherMood } from './types';

export interface WeatherTokens {
  bg: string;
  accent: string;
  border: string;
  glow: string;
  label: string;
}

export const WEATHER_TOKENS: Record<EmotionalWeatherMood, WeatherTokens> = {
  neutral: {
    bg: '#FAF7F2',
    accent: '#8B7355',
    border: '#E4DCD0',
    glow: 'transparent',
    label: 'Neutral',
  },
  joyful: {
    bg: '#FBF6ED',
    accent: '#C4923D',
    border: '#E8DFC8',
    glow: 'rgba(196,146,61,0.04)',
    label: 'Joyful',
  },
  tender: {
    bg: '#F9F3F0',
    accent: '#A67B6B',
    border: '#E6D8D2',
    glow: 'rgba(166,123,107,0.04)',
    label: 'Tender',
  },
  playful: {
    bg: '#F5F5EE',
    accent: '#7A8B5A',
    border: '#DCE0CC',
    glow: 'rgba(122,139,90,0.04)',
    label: 'Playful',
  },
  tense: {
    bg: '#F5F2F0',
    accent: '#8C7B7B',
    border: '#DDD6D3',
    glow: 'rgba(140,123,123,0.04)',
    label: 'Tense',
  },
  latenight: {
    bg: '#F0EDE8',
    accent: '#6B6B8B',
    border: '#D4D0DC',
    glow: 'rgba(107,107,139,0.06)',
    label: 'Late night',
  },
  morning: {
    bg: '#F8F6EE',
    accent: '#8B8A5A',
    border: '#E0DFC8',
    glow: 'rgba(139,138,90,0.04)',
    label: 'Morning',
  },
  missing: {
    bg: '#F4F0ED',
    accent: '#9B7B6B',
    border: '#DBD3CC',
    glow: 'rgba(155,123,107,0.05)',
    label: 'Missing',
  },
};

export function getMoodFromHour(hour: number): EmotionalWeatherMood {
  if (hour >= 1 && hour <= 5) return 'latenight';
  if (hour >= 6 && hour <= 10) return 'morning';
  return 'neutral';
}

export function getWeatherStyle(mood: EmotionalWeatherMood): React.CSSProperties {
  const tokens = WEATHER_TOKENS[mood];
  return {
    '--weather-bg': tokens.bg,
    '--weather-accent': tokens.accent,
    '--weather-border': tokens.border,
    '--weather-glow': tokens.glow,
  } as React.CSSProperties;
}

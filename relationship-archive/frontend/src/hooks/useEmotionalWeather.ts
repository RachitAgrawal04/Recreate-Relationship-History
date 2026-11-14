'use client';

import { useState, useCallback } from 'react';
import type { EmotionalWeatherMood } from '@/lib/types';

export function useEmotionalWeather(initialMood: EmotionalWeatherMood = 'neutral') {
  const [mood, setMood] = useState<EmotionalWeatherMood>(initialMood);

  const updateMood = useCallback((newMood: EmotionalWeatherMood) => {
    setMood(newMood);
  }, []);

  return { mood, updateMood };
}

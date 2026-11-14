'use client';

import { useState, useCallback } from 'react';

export function useMediaReveal(initiallyHidden = true) {
  const [revealed, setRevealed] = useState(!initiallyHidden);

  const reveal = useCallback(() => setRevealed(true), []);
  const hide = useCallback(() => setRevealed(false), []);
  const toggle = useCallback(() => setRevealed((v) => !v), []);

  return { revealed, reveal, hide, toggle };
}

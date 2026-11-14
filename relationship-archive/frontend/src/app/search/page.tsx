'use client';

import { useState, useCallback } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import { SearchBar, SearchResults } from '@/components/search/SearchComponents';
import type { Message } from '@/lib/types';

interface SearchResult {
  message: Message;
  score: number;
}

export default function SearchPage() {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [query, setQuery] = useState('');

  const handleResults = useCallback(
    (newResults: SearchResult[], newQuery: string) => {
      setResults(newResults);
      setQuery(newQuery);
    },
    []
  );

  return (
    <>
      <PageHeader title="Search" subtitle="38,558 messages" />
      <div className="max-w-2xl mx-auto">
        <SearchBar onResults={handleResults} />
        <div
          className="h-px mx-4 lg:mx-8 mb-4"
          style={{ backgroundColor: 'var(--weather-border, #E4DCD0)' }}
        />
        <SearchResults results={results} query={query} />
      </div>
    </>
  );
}

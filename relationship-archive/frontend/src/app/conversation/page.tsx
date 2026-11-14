import PageHeader from '@/components/layout/PageHeader';
import ChatThread from '@/components/chat/ChatThread';
import { FIXTURE_MESSAGES } from '@/lib/fixtures';

export default function ConversationPage() {
  // For the demo, show all fixture messages sorted by time
  const sorted = [...FIXTURE_MESSAGES].sort(
    (a, b) =>
      new Date(a.timestamp_parsed).getTime() -
      new Date(b.timestamp_parsed).getTime()
  );

  return (
    <>
      <PageHeader
        title="Conversation"
        subtitle="Full archive — synthetic preview"
        right={
          <div className="flex items-center gap-2">
            <span
              className="text-[0.6rem] font-bold uppercase tracking-widest px-2 py-1 rounded"
              style={{ color: '#6B8F71', backgroundColor: 'rgba(107,143,113,0.1)' }}
            >
              WA
            </span>
            <span
              className="text-[0.6rem] font-bold uppercase tracking-widest px-2 py-1 rounded"
              style={{ color: '#8B6B8F', backgroundColor: 'rgba(139,107,143,0.1)' }}
            >
              IG
            </span>
          </div>
        }
      />

      {/* Bubble legend */}
      <div
        className="flex items-center gap-4 px-4 lg:px-8 py-2 text-xs text-[#9C9184] border-b"
        style={{ borderColor: 'var(--weather-border, #E4DCD0)' }}
      >
        <span className="flex items-center gap-1.5">
          <span
            className="inline-block w-3 h-3 rounded-sm"
            style={{ backgroundColor: '#E8DED2' }}
          />
          Rachit (left)
        </span>
        <span className="flex items-center gap-1.5">
          <span
            className="inline-block w-3 h-3 rounded-sm"
            style={{ backgroundColor: '#DDE4DB' }}
          />
          Radhika (right)
        </span>
      </div>

      <div className="max-w-2xl mx-auto">
        <ChatThread messages={sorted} />
      </div>

      {/* Load more placeholder */}
      <div className="flex justify-center py-8 px-4">
        <button
          className="px-6 py-2.5 rounded-xl border text-sm text-[#6B6259] hover:bg-[#F3EDE4] transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1"
          style={{
            borderColor: 'var(--weather-border, #E4DCD0)',
            '--tw-ring-color': '#7B8BA0',
          } as React.CSSProperties}
          disabled
          aria-label="Load earlier messages — real data not yet integrated"
        >
          Load earlier messages
          <span className="ml-2 text-xs text-[#9C9184]">(real data pending)</span>
        </button>
      </div>
    </>
  );
}

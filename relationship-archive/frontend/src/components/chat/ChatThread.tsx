import type { Message } from '@/lib/types';
import ChatBubble from './ChatBubble';
import { formatDate, isSameDay, isGroupedWith } from '@/lib/utils';

function DayHeader({ dateStr }: { dateStr: string }) {
  return (
    <div className="flex items-center gap-3 my-6">
      <div className="flex-1 h-px" style={{ backgroundColor: 'var(--weather-border, #E4DCD0)' }} />
      <span
        className="text-[0.6875rem] font-semibold uppercase tracking-widest px-3 py-1 rounded-full border"
        style={{
          color: '#9C9184',
          borderColor: 'var(--weather-border, #E4DCD0)',
          backgroundColor: 'var(--weather-bg, #FAF7F2)',
        }}
      >
        {formatDate(dateStr + 'T00:00:00+05:30')}
      </span>
      <div className="flex-1 h-px" style={{ backgroundColor: 'var(--weather-border, #E4DCD0)' }} />
    </div>
  );
}

interface ChatThreadProps {
  messages: Message[];
  showPlatformBadge?: boolean;
}

export default function ChatThread({ messages, showPlatformBadge = true }: ChatThreadProps) {
  if (!messages.length) {
    return (
      <div className="flex items-center justify-center py-20 text-[#9C9184] text-sm">
        No messages.
      </div>
    );
  }

  const rendered: React.ReactNode[] = [];
  let lastDateKey = '';

  messages.forEach((msg, i) => {
    const dateKey = msg.timestamp_parsed.substring(0, 10);
    const prev = messages[i - 1];
    const next = messages[i + 1];

    // Day separator
    if (dateKey !== lastDateKey) {
      rendered.push(<DayHeader key={`day-${dateKey}`} dateStr={dateKey} />);
      lastDateKey = dateKey;
    }

    const grouped = !!prev && isGroupedWith(prev, msg);
    const nextGrouped = !!next && isGroupedWith(msg, next);
    const isFirst = !grouped;
    const isLast = !nextGrouped;

    rendered.push(
      <ChatBubble
        key={msg.event_id}
        message={msg}
        isGrouped={grouped}
        isFirstInGroup={isFirst}
        isLastInGroup={isLast}
        showPlatformBadge={showPlatformBadge}
      />
    );
  });

  return <div className="px-4 lg:px-8 py-4">{rendered}</div>;
}

import PageHeader from '@/components/layout/PageHeader';
import ChapterCard from '@/components/chapters/ChapterCard';
import { FIXTURE_CHAPTERS } from '@/lib/fixtures';

export default function ChaptersPage() {
  return (
    <>
      <PageHeader
        title="Chapters"
        subtitle="Four arcs across six months"
      />
      <div className="px-4 lg:px-8 py-6 max-w-4xl mx-auto">
        <p
          className="font-serif italic text-base text-[#6B6259] leading-relaxed mb-8 max-w-lg"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          Every relationship has chapters. This one has four — each with its
          own texture, pace, and emotional weight.
        </p>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {FIXTURE_CHAPTERS.map((chapter) => (
            <ChapterCard key={chapter.id} chapter={chapter} />
          ))}
        </div>
      </div>
    </>
  );
}

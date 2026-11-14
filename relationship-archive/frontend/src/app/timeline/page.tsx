import PageHeader from '@/components/layout/PageHeader';
import TimelineTrack from '@/components/timeline/TimelineTrack';
import { FIXTURE_TIMELINE } from '@/lib/fixtures';

export default function TimelinePage() {
  return (
    <>
      <PageHeader
        title="Timeline"
        subtitle="May – November 2026"
      />
      <TimelineTrack months={FIXTURE_TIMELINE} />
    </>
  );
}

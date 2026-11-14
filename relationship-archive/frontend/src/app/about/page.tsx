import PageHeader from '@/components/layout/PageHeader';
import { ARCHIVE_STATS } from '@/lib/fixtures';
import { formatNumber, formatShortDate } from '@/lib/utils';

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-10">
      <h2
        className="text-[0.6875rem] font-bold uppercase tracking-widest mb-4"
        style={{ color: 'var(--weather-accent, #8B7355)' }}
      >
        {title}
      </h2>
      {children}
    </section>
  );
}

function DataRow({ label, value }: { label: string; value: string }) {
  return (
    <div
      className="flex items-center justify-between py-3 border-b text-sm"
      style={{ borderColor: 'var(--weather-border, #E4DCD0)' }}
    >
      <span className="text-[#6B6259]">{label}</span>
      <span className="font-medium text-[#1A1714] tabular-nums">{value}</span>
    </div>
  );
}

export default function AboutPage() {
  return (
    <>
      <PageHeader title="About This Archive" subtitle="Methodology & credits" />

      <div className="max-w-xl mx-auto px-4 lg:px-8 py-8">
        {/* Intro */}
        <p
          className="font-serif italic text-lg text-[#6B6259] leading-relaxed mb-10"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          This archive contains every message, photo, and moment exchanged
          between Rachit Agrawal and Radhika Singhal across Instagram and
          WhatsApp, from May to November 2026.
        </p>

        {/* Data sources */}
        <Section title="Data Sources">
          <DataRow label="WhatsApp messages" value={formatNumber(ARCHIVE_STATS.whatsapp_messages)} />
          <DataRow label="Instagram messages" value={formatNumber(ARCHIVE_STATS.instagram_messages)} />
          <DataRow label="Total messages" value={formatNumber(ARCHIVE_STATS.total_messages)} />
          <DataRow label="Media items" value={formatNumber(ARCHIVE_STATS.media_items)} />
          <DataRow label="Days of conversation" value={String(ARCHIVE_STATS.total_days)} />
          <DataRow
            label="Archive begins"
            value={formatShortDate(ARCHIVE_STATS.date_start + 'T00:00:00+05:30')}
          />
          <DataRow
            label="Archive ends"
            value={formatShortDate(ARCHIVE_STATS.date_end + 'T00:00:00+05:30')}
          />
        </Section>

        {/* How it was built */}
        <Section title="How It Was Built">
          <div className="space-y-3 text-sm text-[#6B6259] leading-relaxed">
            <p>
              Raw exports were collected from WhatsApp (text + media export) and
              Instagram (data download). A Python ingestion pipeline parsed,
              normalised, and merged both sources into a unified event stream of
              38,558 messages — preserving original timestamps, sender identity,
              message ordering, and media references.
            </p>
            <p>
              All 910 media files were inventoried, hashed, and cross-referenced
              with their originating messages. 37 messages with generic
              &ldquo;&lt;Media omitted&gt;&rdquo; markers are noted as
              irrecoverable gaps.
            </p>
            <p>
              The website uses Next.js 15 with TypeScript. No data is loaded
              server-side from a database — the archive is read locally at
              runtime. No third-party analytics, no external fonts loaded without
              consent.
            </p>
          </div>
        </Section>

        {/* Visual system */}
        <Section title="Visual System">
          <div className="space-y-2 text-sm text-[#6B6259]">
            <p>
              <span className="font-medium text-[#1A1714]">Typography</span>
              {' — '}Source Serif 4, Inter, Noto Sans Devanagari, JetBrains Mono
            </p>
            <p>
              <span className="font-medium text-[#1A1714]">Colour</span>
              {' — '}Warm linen base with eight emotional weather states
            </p>
            <p>
              <span className="font-medium text-[#1A1714]">Message bubbles</span>
              {' — '}Rachit: warm umber left-aligned. Radhika: sage right-aligned.
            </p>
          </div>
        </Section>

        {/* Privacy */}
        <Section title="Privacy">
          <div
            className="rounded-xl border px-5 py-4 text-sm text-[#6B6259] leading-relaxed space-y-2"
            style={{
              backgroundColor: 'var(--color-bg-secondary, #F3EDE4)',
              borderColor: 'var(--weather-border, #E4DCD0)',
            }}
          >
            <p>
              This archive is entirely private. No conversation data, media, or
              personal information has been uploaded to any cloud service, shared
              externally, or made publicly accessible.
            </p>
            <p>
              Original exports remain read-only on local storage. The app serves
              from localhost only.
            </p>
            <p>
              Sensitive media is hidden by default and requires deliberate
              interaction to reveal. AI analysis runs locally.
            </p>
          </div>
        </Section>

        {/* Phase status */}
        <Section title="Current Status">
          <div className="space-y-1.5 text-sm">
            {[
              ['Ingestion pipeline', 'Complete ✅'],
              ['Design system', 'Complete ✅'],
              ['Frontend scaffold', 'Complete ✅'],
              ['Synthetic preview', 'Live ✅'],
              ['Real data integration', 'Pending user approval ⏳'],
              ['AI analysis pass', 'Pending ⏳'],
              ['Human annotations', 'Pending ⏳'],
            ].map(([label, val]) => (
              <div key={label} className="flex justify-between py-2 border-b" style={{ borderColor: 'var(--weather-border, #E4DCD0)' }}>
                <span className="text-[#6B6259]">{label}</span>
                <span className="text-[#9C9184]">{val}</span>
              </div>
            ))}
          </div>
        </Section>
      </div>
    </>
  );
}

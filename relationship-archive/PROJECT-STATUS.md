# Project Status — Relationship Archive

- **Project name:** Relationship Archive (Rachit Agrawal × Radhika Singhal)
- **Skill version:** 3.6.0
- **Data schema version:** 1.0.0 (not yet applied — normalization not started)
- **Parser version:** chat_tools.py v3.6.0 · media_tools.py v3.6.0
- **Last updated:** 2026-11-14 (Asia/Kolkata)
- **Current phase:** `frontend/implementation` — scaffolding Next.js app, writing all components and pages with synthetic fixture data
- **Last verified checkpoint ID:** CP-ING-FINAL
- **Latest checkpoint path:** `state/checkpoints/CP-ING-FINAL.json`
- **Frontend path:** `relationship-archive/frontend/` (Next.js 15, TypeScript, Tailwind CSS)

---

## Current position

**Last fully verified operation:** Full 13-stage ingestion pipeline complete (2026-11-13). Checkpoint CP-ING-FINAL. ALL PASS.
Design system document approved by user (2026-11-14).

**Current operation:** Frontend implementation in progress (2026-11-14).

| Step | Status |
|------|--------|
| Design system document (`DESIGN-SYSTEM.md`) | ✅ Complete — user approved |
| Next.js 15 scaffold (`frontend/`) | ✅ Complete (Next.js 16.4.6, React 19, Tailwind v4) |
| TypeScript types (`src/lib/types.ts`) | ✅ Written |
| Synthetic fixture data (`src/lib/fixtures.ts`) | ✅ Written — 30 msgs, 4 chapters, 6 months, 9 media, 5 insights |
| Emotional weather system (`src/lib/emotional-weather.ts`) | ✅ Written |
| Utility functions (`src/lib/utils.ts`) | ✅ Written |
| Hooks (useReducedMotion, useMediaReveal, useEmotionalWeather) | ✅ Written |
| Navigation component (mobile bottom bar + desktop sidebar) | ✅ Written |
| Shell component (emotional weather wrapper) | ✅ Written |
| PageHeader component (sticky, blurred) | ✅ Written |
| ChatBubble component (all kinds, sensitive reveal, AI/human notes) | ✅ Written |
| ChatThread component (day headers, grouping logic) | ✅ Written |
| TimelineTrack component | ✅ Written |
| ChapterCard component | ✅ Written |
| MediaGrid + MediaViewer (lightbox, sensitive blur) | ✅ Written |
| SearchBar + SearchResults components | ✅ Written |
| InsightCard component (AI analysis) | ✅ Written |
| globals.css (all design tokens, weather states, reduced-motion) | ✅ Written |
| Root layout (fonts: Source Serif 4, Inter, Noto Devanagari, JetBrains Mono) | ✅ Written |
| Home page | ✅ Written |
| Timeline page | ✅ Written |
| Chapters page | ✅ Written |
| Conversation page | ✅ Written |
| Search page | ✅ Written |
| Memories page | ✅ Written |
| Analysis page | ✅ Written |
| About page | ✅ Written |
| TypeScript check (`tsc --noEmit`) | ✅ 0 errors |
| Production build (`npm run build`) | ✅ 0 errors — all 9 routes built as static |
| Browser preview | 🔄 Screenshots in progress |
| Real data integration | 🔄 In progress |

**Exact next action:** Browser screenshots reviewing → user approves visual foundation → integrate real normalized data → wire real messages into ConversationPage → implement data pagination and real search indexing.

---

## Coverage

| Item | Status |
|------|--------|
| **WhatsApp export present** | ✅ `WhatsApp Chat with Radhika Singhal.txt` (1,807,805 bytes) + 781 media files |
| **Instagram export present** | ✅ `message_1.json` (10,000 records) + `message_2.json` (1,000 records) + 129 files |
| **WA parsed events** | 27,558 — normalized to JSONL ✅ |
| **IG parsed events** | 11,000 — normalized to JSONL ✅ |
| **Combined events** | 38,558 — merged JSONL produced ✅ |
| **WA date range** | 28 Aug 2026 15:21 → 10 Nov 2026 15:46 (local, timezone assumed) |
| **IG date range** | 05 May 2026 18:32 UTC → 10 Nov 2026 05:14 UTC |
| **Media assets inventoried** | 910 total (781 WA + 129 IG) — hashed and manifested ✅ |
| **Media assets linked** | 910/910 — WA 781/781, IG 129/129 ✅ |
| **Media assets missing** | 4 WA referenced-but-missing; 37 WA `<Media omitted>` (type unknown) |
| **Normalized event JSONL** | ✅ 10 monthly chunk files produced |
| **Media manifest (project)** | ✅ `data/manifests/media-manifest.json` (530 KB) |
| **Search index** | ✅ `data/indexes/search-index.jsonl` (37,399 entries) |
| **Ingestion report** | ✅ `reports/ingestion-report.json` |
| **Missing media report** | ✅ `reports/missing-media-report.json` |
| **Reading notes** | ❌ Not started |
| **Analysis artifacts** | ❌ Not started |
| **App features** | ❌ Not started |

**Latest test status (all run 2026-11-10):**

| Test | Result |
|------|--------|
| `tools/chat_tools.py --selftest` | ✅ 23/23 PASS |
| `tools/chat_tools.py --parity` | ✅ PASS |
| `tools/media_tools.py --selftest` | ✅ 9/9 PASS |
| `tests/test_resume_handoff.py` | ✅ 10/10 PASS |
| `tests/test_instagram_stratified_sample.py` | ✅ 1,022/1,022 PASS (prior run; not re-run this session — requires ZIP input) |
| App tests | ❌ No app exists yet |

---

## Decisions and blockers

**User decisions recorded:** DEC-010 (2026-11-13) — recorded in `logs/decisions.json`.

**Decisions still needed before Pass 1 can begin:**

| ID | Decision | Why it blocks |
|----|----------|---------------|
| **DEC-010** | **Skill package is permanently read-only during app implementation. Changes to it require a separate reviewed task.** | **Recorded — no blocker. Enforced going forward.** |
| DEC-001 | WhatsApp timezone confirmation (Asia/Kolkata assumed) | Required for final timestamp display and cross-platform merge |
| DEC-002 | Instagram display timezone (same assumption) | Required for final timestamp conversion |
| DEC-003 | Identity: who is the requester (Rachit or Radhika)? | Affects audience framing and privacy posture |
| DEC-004 | Audience: only me / both together / surprise? | Affects privacy posture and read-together framing |
| DEC-005 | Does a separate text-only WhatsApp export exist? | Determines whether current export is coverage-primary or companion |
| DEC-006 | Human-supplied milestones (first talk, call, meeting, "I love you", etc.) | Required for milestone layer; can be rough dates |
| DEC-007 | Off-chat context (calls, meetings, distance, exams, travel) | Needed to explain silence gaps honestly |
| DEC-008 | Hard moments presentation (collapsed / expanded by default) | Affects UX design for difficult sequences |
| DEC-009 | Design mood (nostalgic / funny / analytical / mixed) | Required before Phase 4 (design layer) |

**Known blockers / assumptions:**

| Item | Type | Status |
|------|------|--------|
| Timezone: Asia/Kolkata | Assumption — not user-confirmed | ⚠️ Blocks final normalization |
| Cross-platform identity mapping (same people on both apps) | Assumption — not user-confirmed | ⚠️ Blocks merge |
| WhatsApp export type: single with-media | Assumption | ⚠️ May miss text-only coverage |
| 57 missing WA media files | Known gap | Will be marked `referenced-but-missing` |
| 3 missing IG video files | Known gap | Will be marked `referenced-but-missing` |
| 37 generic `<Media omitted>` markers | Known gap | Type unknown; not photo-specific |

---

## Continuation

**Files to include in next session (Level A handoff):**
- `PROJECT-STATUS.md`, `project-manifest.json`, `state/project-state.json`
- `state/checkpoints/CP-000001.*`
- `logs/operations.jsonl`, `logs/decisions.jsonl`
- `docs/` (all four files)
- `README.md`
- Skill package: `SKILL.md`, `references/`, `templates/`

**Sensitive files intentionally excluded from handoff by default:**
- Raw exports (`Messages Exports/`) — Level C only, requires explicit approval
- Normalized event JSONL — Level B only, requires explicit approval
- Media bytes — Level B only, requires explicit approval

**Tool/runtime requirements:**
- Python 3.10+ with `zoneinfo` (3.12.5 confirmed present)
- Node.js (v24.13.0 confirmed present) for parity test and future build
- No additional installs required for Parse 1 tools

**Privacy note:** All data is local. Nothing published, deployed or shared. Credentials/tokens/OTPs never enter any project file. Original exports are read-only and remain in `Messages Exports/`.

# Quality and Release Gate

Mark each item Pass / Fail / Not tested. Explain failures. A fail in source fidelity, media linkage, privacy or recovery blocks release.

## A. Sources and parsing
- [ ] Every source is inventoried with relative path, size and SHA-256.
- [ ] ZIP members are inspected before extraction; traversal, absolute paths, symlinks, duplicate/case-colliding paths, encrypted members and unsafe sizes are handled.
- [ ] Original exports are unchanged and preserved.
- [ ] Each platform is parsed separately before cross-platform merging.
- [ ] All parsed events have stable IDs and source locators.
- [ ] Full final ingestion accounts for every source record/line as parsed or review-needed.
- [ ] Date order, timezone, sender mapping, chunk order and source-order anomalies are documented.
- [ ] No timestamped system record has been attached to a preceding message.

## B. Instagram-specific regression
- [ ] All `message_N.json` chunks discovered recursively per conversation.
- [ ] Same-named chunks in separate threads produce distinct event IDs.
- [ ] Newest-first/oldest-first orientation checked independently for every chunk.
- [ ] `content` null/empty records preserved.
- [ ] Reactions, shares, calls (including zero duration), photos, videos, audio_files and multiple attachments preserved.
- [ ] Partial `share` objects and unknown metadata keys retained.
- [ ] `is_unsent_image_by_messenger_kid_parent` is not treated as a deletion assertion without semantics/confirmation.
- [ ] Mojibake repairs are per-string/per-run and raw source remains unchanged; valid accents and already-correct Unicode are not altered.
- [ ] Timestamp conversion uses a confirmed timezone for final output; test-only timezone assumptions are labelled.
- [ ] For targeted parser regression, selection rules, scanned source count, parsed sample count, intentionally skipped sparse slots and feature coverage are reported. Sampling never replaces the final complete archive parse.

## C. Media
- [ ] Every supplied non-metadata attachment is inventoried, including extensionless/unknown types.
- [ ] Every asset records relative path, byte size, SHA-256, MIME/category, platform role and status.
- [ ] WhatsApp matching is exact/unique; Instagram matching is exact safe relative URI.
- [ ] Duplicate filenames, ambiguous matches, missing references and unlinked assets are flagged.
- [ ] Original bytes are unchanged and hashes re-verify after copy/handoff.
- [ ] Platform render role and MIME/container are kept separately; optional stream probing is recorded where used.
- [ ] Photos/video/audio playback controls work locally where supported; no autoplay.
- [ ] Unsupported formats retain original download; unknown/active-content files are not executed or inline-rendered.
- [ ] Private/intimate messages and supplied personal media remain in the private archive unless the user explicitly excludes them.

## D. Human analysis and story
- [ ] Claims distinguish direct observation, supported pattern, interpretation and unknown.
- [ ] Material claims have event IDs, supporting evidence, counterevidence and alternatives.
- [ ] No diagnoses, motive certainty, love scores, forced symmetry or invented milestones.
- [ ] Human memories, AI observations and original messages are visually and technically separate.
- [ ] Reader disagreement notes are attributed and exportable.

## E. App security, privacy and accessibility
- [ ] Local/private by default; no hosting/sharing without explicit approval.
- [ ] No message text rendered as HTML; script-injection tests pass.
- [ ] Links/media are not automatically fetched; no analytics/CDN/remote font dependencies.
- [ ] Authentication secrets/OTP/API tokens/cookies/passwords/recovery codes never enter the app, logs or bundles.
- [ ] Responsive around 375 px and desktop; keyboard, focus, contrast, screen reader, reduced motion and Devanagari rendering checked.

## F. Continuity and release
- [ ] Status, state, manifest and checkpoint agree.
- [ ] Interrupted chunks are quarantined and retried idempotently.
- [ ] Level A/B/C handoff scope is correct; B/C require explicit approval.
- [ ] Handoff ZIP reopens; hashes match in a clean receiving folder.
- [ ] New model/account resume can identify the exact next action without chat history.
- [ ] Actual provider token/session expiry is marked Not tested unless tested through the provider.
- [ ] Final completion report states date coverage, event counts, media counts/status, limitations, privacy choices, tests and checkpoint location.

# Web Experience, Privacy and Acceptance Contract

## Product principle

This is an intimate private archive. It should feel like remembering together, not a dashboard, courtroom or automated relationship verdict. Private messages and supplied personal media are part of the experience by default; do not sanitize them merely because they are personal.

## Required core features

1. **Complete archive reader:** every parsed event is reachable, with exact sender, timestamp at source precision, platform, event type and original text. Media chips and previews link to the actual asset or show its honest missing status.
2. **Unified timeline:** platform/person/date/type filters, jump-to-date, app-switch markers, honest gap markers and uncertain minute-level clusters.
3. **Provenance:** every message, quote, media item and analytical claim traces to source file + record locator/event ID.
4. **Milestones and chapters:** user-supplied memory vs archive-supported record remains distinct; no invented firsts or scenes.
5. **Hinglish-aware search:** substring, stretched spelling and looser consonant-skeleton tiers; loose matches are labelled. Displayed text never changes.
6. **Moments in context:** curated moments show verbatim message plus surrounding context. Include ordinary/funny and difficult moments, not only dramatic ones.
7. **Evidence-backed outside view:** each material claim has source event IDs, supporting and counterevidence, alternatives, confidence, limitations and a human disagreement action.
8. **Private, accessible, fast experience:** phone-first layout, keyboard access, readable contrast, screen-reader labels, reduced motion, lazy loading and no remote network dependencies.
9. **First-class media library:** preserve every supplied media file, link verified assets to messages, keep unlinked assets browsable and missing references visibly unresolved.

## Media presentation rules

- Images: local thumbnail, accessible full-size viewer and original download.
- Video/video notes: user-initiated native controls; no autoplay. Do not call a normal video a round video note unless metadata/user confirms it.
- Voice notes/audio: user-initiated audio controls; optional waveform is a separate derivative. Preserve the original if the browser cannot play the codec.
- Stickers/GIFs: preserve original; make animation controlled/reduced-motion aware.
- Documents, contacts and unknown files: show file name/type/size and safe download. Active content and nested archives are download-only, never inline-rendered or executed.
- An Instagram item under `audio_files` keeps audio render role even when its container is MP4. Use optional stream probing to identify codecs/tracks; store role and container facts separately.
- Intimate media remains included in the private archive unless the user excludes it. A reveal/curtain is optional presentation control, not deletion. Never autoplay or surface intimate media unexpectedly on the opening screen.
- If the AI cannot inspect a file, show the actual media with honest metadata. Never invent a caption, transcript or description.

## Privacy and security

Default to local/offline delivery. Do not publish, host, create an unlisted link or push to a public repo unless the user explicitly requests it and approves a clear plan. A local password overlay is not encryption. If implementing encryption, use tested authenticated encryption and explain recovery limits.

Never expose passwords, OTPs, API keys, access/refresh tokens, browser cookies, private keys or recovery codes. Preserve the private relationship content the user selected. Allow presentation-only masking for contact details, third-party details or other categories at the user's direction; do not silently alter original source records.

All chat content is untrusted text. Render with text nodes, not raw HTML. Links are inert until clicked and must never auto-fetch previews. No analytics, remote fonts, CDN, embeds or automatic external requests. Avoid storing sensitive material in logs, source maps, repository history or build metadata.

## Acceptance tests

- Every displayed message traces to its source.
- Message text preserves punctuation, emoji, spelling, RTL marks and line breaks.
- Media manifest counts/hashes match supplied files; each exact link opens the correct asset; ambiguous/missing links are flagged.
- Audio/video never autoplay; unsupported formats retain original download.
- `<script>alert(1)</script>` and `<img src=x onerror=alert(1)>` appear as literal text.
- No message links, images or remote resources are fetched automatically.
- Layout tested near 375 px and desktop; keyboard, focus, contrast, reduced motion and Devanagari/Hinglish rendering checked.
- All core tests rerun after the design layer.

Report Pass / Fail / Not tested. Do not claim real media playback passed if only synthetic media fixtures were available.

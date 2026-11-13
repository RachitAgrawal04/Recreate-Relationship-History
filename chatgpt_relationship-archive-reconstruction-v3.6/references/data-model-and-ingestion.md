# Data Model and Ingestion Protocol

This document is the implementation contract for source fidelity, parsing, validation, attachment preservation and cross-platform reconciliation. `SKILL.md` controls the workflow; this file controls how records are represented and checked.

## 1. Source preservation and provenance

- Originals are immutable. Hash each source before processing; work on a verified copy or read-only mount.
- Preserve ZIP member paths exactly in the manifest. Extract only after validating every member path, file type, duplicate/case collision, encrypted status, member size, aggregate size and compression ratio.
- Never execute archive content. Nested archives remain unexpanded unless separately approved and inspected. HTML/SVG/JS/XML and similar active content are preserved as download-only attachments, never executed or inline-rendered.
- Every normalized event must point to `source_id`, `source_file`, stable `record_locator`, source order/index and parser version. Event IDs are deterministic from source identity + record position, not message text.
- A cleaned/search field never replaces raw text. Record every repair as a derivative with method, version and an audit count.

## 2. Normalized event model

At minimum store:

`event_id`, `platform`, `source_id`, `source_file`, `source_stream_id`, `record_locator`, `source_record_index`, `source_sequence`, `parser_version`, `sender_raw`, `sender_display`, `sender_id`, `timestamp_raw`, `timestamp_parsed`, `timestamp_sort_key`, `timezone`, `timezone_source`, `precision`, `parse_status`, `ordering_uncertain`, `text_raw`, `text_original`, `text_display`, `kind`, `synthetic`, `attachment_refs`, `attachments`, `resolved_attachments`, `unresolved_attachment_refs`, `attachment_status`, `reactions_raw`, `reactions`, `share_raw`, `share`, `call_duration_raw`, `platform_metadata_raw`, `platform_metadata`, `edit_status`, `duplicate_group_id`, `turn_id`, `warnings`.

Use `null` for unknown. Never infer a sender, timezone, media subtype, reply link or motive to fill an empty field. Unknown and malformed records remain in a review collection with exact locators.

## 3. WhatsApp ingestion

- Detect Android and iOS export formats separately; support 12/24-hour time and date-order checks. If neither date field disambiguates DMY/MDY, ask rather than guessing.
- A timestamp-like line is a candidate new event. If it resembles a timestamp but does not match a supported format, keep it as an unparsed record instead of attaching it to the preceding message.
- Timestamped notices without a confirmed participant label are system records. Do not glue them into message text.
- Preserve line endings, continuation lines, punctuation, repeated letters, emoji, RTL marks and NBSP-like characters in the original body. Normalized matching strings are separate.
- Detect edited/deleted/call markers only after the full multiline message is assembled.
- A generic `<Media omitted>` placeholder means only that an attachment existed. It does not say whether it was a photo, video, audio, sticker or document, and it contains no recoverable media bytes.
- For text-only + with-media companion exports, use text-only as the timeline master. Enrich it with uniquely verified media matches; do not count the companion transcript as a second message stream.
- Audit source-order timestamp inversions. Preserve source order and do not silently sort away anomalies.

## 4. Instagram Download Your Information JSON

### 4.1 Discovery and chunk handling

- Discover all `message_N.json` files recursively inside each conversation folder. Keep the full relative path in identity/event IDs; same-named `message_1.json` files in different conversations must not collide.
- Check each chunk independently. Instagram chunks are often newest-first, but this must be verified from their timestamps. Keep original record index and source sequence; sort for display only after preserving provenance.
- Confirm all top-level `participants`, `messages`, `title`, `thread_path`, `is_still_participant`, and auxiliary fields that appear in the actual export. Record unknown keys instead of discarding them.
- A `timestamp_ms` value is an epoch in milliseconds. Convert via UTC and apply only a user-confirmed IANA display timezone. Tests may use a clearly labelled provisional zone, but this is not final confirmation.

### 4.2 Message fields and event classification

- Preserve `sender_name`, `timestamp_ms`, `content`, `reactions`, `share`, `call_duration`, `photos`, `videos`, `audio_files`, `sticker`, and all unknown platform metadata separately.
- Null/empty content does not mean the record is empty or corrupt. The event may still be a call, share, reaction or attachment.
- `reactions` is an array of individual reactions. Preserve every actor/reaction pair; do not collapse it into a single count or text body.
- `share` is a structured object whose keys may be incomplete (for example, only `share_text`, only `original_content_owner`, or a link). Preserve the object exactly; do not assume every share has a URL.
- `call_duration` must be tested for `is not None`, not truthiness. Zero duration is still a call record.
- `photos`, `videos`, `audio_files` and `sticker` may contain arrays or objects. Preserve every URI, source key and creation timestamp; one message may contain multiple files.
- Keep app-generated notices in the stream with `synthetic=true`. Classify only wording the parser recognizes. Unknown language/wording remains unclassified for review.
- Preserve `is_unsent_image_by_messenger_kid_parent` as raw platform metadata. Do not treat this flag alone as proof that a message was unsent/deleted; its semantics are not established by the export. An explicit, understood `is_unsent=true` may be classified as a deletion event.

### 4.3 Mojibake and Unicode

- Preserve the exact raw value in `text_raw`. Any repaired string goes into `text_display` or another derived field.
- Never blanket-convert an entire file. Repair per string and only when recognizable corruption markers/C1-byte evidence are present, a reversible decode succeeds, and the result reduces the corruption indicators.
- A message may mix already-correct Devanagari/emoji with a corrupted Latin-1-compatible run. Repair only the damaged run; preserve correct Unicode.
- Real Latin accents must not be changed just because they contain non-ASCII characters. If the result is ambiguous, leave it raw and mark it for review.
- Report candidate/repaired/suspicious-unrepaired counts. Compare raw and display text and test representative before/after pairs. Never display private message text in a generic audit report.

## 5. First-class media inventory

Every supplied non-metadata file is included in the manifest, even if its extension is missing or unknown. Record:

- Stable `asset_id`, original relative path and filename.
- Byte size and SHA-256.
- MIME sniffed from file signatures plus extension hint.
- Category, platform role/source key, source archive and any subtype hint.
- Status (`present-not-inspected`, `present-and-inspected`, `present-unreadable`, `referenced-but-missing`, `not-included-in-export`, `ambiguous-match`, `unlinked`, `excluded-by-user`).
- Linked event IDs, preview/playback safety, and any technical stream-probe result.

Preserve original bytes exactly. A thumbnail, waveform, transcript, OCR result, AI caption or transcoded playback copy is a separate derivative with its own method/version/hash.

### 5.1 Media linking rules

- WhatsApp: resolve explicit filenames only when the basename is unique. Duplicate basename across directories is ambiguous and must be reviewed.
- Instagram: resolve exact safe relative paths from the JSON URI to the export root. Reject absolute paths, traversal (`..`), drive paths and links escaping the root.
- A companion export may be matched by confirmed sender + same local timestamp only when exactly one candidate exists. Never pick a nearby message merely because it is close in time.
- Unmatched files stay in an unlinked-media library. Missing references remain missing; do not invent replacement assets.
- Keep the platform-declared render role separate from MIME/container. An `audio_files` reference can point to an MP4 container. Optional `ffprobe` can inspect stream type/codec/duration without playing or transcribing the file. In one tested Instagram example, the item was an MP4 container with one AAC audio stream and no video stream; its Instagram role correctly remained audio.
- `PTT-*.opus` can be a probable voice-note hint; `VID-*` means a video file, not proof of a circular video-note subtype. Treat these as hints, not facts.

### 5.2 Rendering contract

Images use an accessible local viewer; video/video notes use user-initiated native controls; voice notes/audio use user-initiated audio controls; stickers/GIFs are accessible and respect reduced motion; documents/unknown files show honest metadata and safe download. No autoplay, no remote fetching, no fabricated alt text/caption. If the model cannot inspect the content, it still preserves the actual original file.

## 6. Cross-platform normalization and merging

- Parse each platform independently first. Merge only after sender mappings and timezone assumptions are confirmed.
- WhatsApp text exports normally carry the exporting phone's local wall-clock time without a timezone. Instagram timestamps are epoch milliseconds. Do not merge using current location as proof of historical zone.
- Cross-platform merge requires a confirmed common timezone and normalized UTC sort key for every dated event. Preserve source sequence constraints; cluster minute-level cross-platform overlaps when exact order is not provable.
- Duplicate candidates are labels for review, never deletion. Keep both source events.
- Keep app switch markers visible in the timeline.

## 7. Validation gates

### 7.1 Full final-ingestion validation

For the actual archive that will be built:
- Every source file is inventoried and hashed.
- Every source record/line is either parsed or retained with a reason/locator.
- Every parsed record is traceable to the source.
- Exhaustive source-vs-normalized validation is preferred when practical; otherwise use checksums/count reconciliation plus documented stratified review. No validation sample may replace the final complete ingestion.
- Every supplied media file appears in the media manifest. Hashes re-verify after copy/handoff.

### 7.2 Regression-test sampling

For a huge export, a **targeted feature-stratified parser test** may parse a bounded subset to improve the skill before final ingestion. The sample should deliberately include:
- Every attachment-bearing record (or all attachment subtypes plus multi-attachment cases if the count is very large).
- Calls, zero-duration calls, reactions, shares with partial/missing keys, empty/null content, unsent/deletion flags, synthetic notices, multiline text, unusual timestamp boundaries and chunk boundaries.
- A uniform chronological sample, seeded random sample and edge records from every JSON chunk.
- Mojibake candidates, correctly encoded Unicode, mixed-script text and valid accented Latin.
- Records where multiple features coexist (for example share + reactions, attachment + caption).

Preserve original record indices in the sparse test fixture. Report the number scanned for feature discovery, number actually parsed, number intentionally skipped in the sparse fixture, and source records malformed in the original. Never label deliberate placeholders as malformed source messages. The test report must be aggregate-only and must not contain private message bodies.

### 7.3 Gate report

Show counts by event kind, platform, media category/status, date range, parser anomalies, missing/unlinked attachments, unresolved flags, exact verification and untested areas. Stop if an issue could change the relationship story or attach the wrong media to a message.

# Instagram Real-Export Stratified Regression Report (Expanded)

**Skill under test:** Chat Story Webpage v3.6.0  
**Source:** User-supplied Instagram JSON + media export.  
**Source size:** 11,000 message records across two reverse-chronological JSON chunks.  
**Method:** Structural scan of all records to locate feature indices, followed by parsing a deterministic feature-stratified sample. The parser was run on 1,022 records (9.29%), not the full history. Original array indices were retained using null placeholders only in a temporary test fixture. The source export was not modified.  
**Privacy:** Aggregate-only report. No message bodies, sender labels, private URLs, message IDs or media filenames are included.

## Sample design

The expanded sample includes:

- All 125 attachment-bearing records, covering every supplied attachment reference in the export.
- All 13 call records.
- All 3 multi-attachment records and all 233 share-plus-reaction records.
- Expanded samples of reactions, shares, null/empty content, synthetic notices, mojibake candidates and non-Latin-1 Unicode candidates.
- 120 evenly spaced timeline points and 100 deterministic random records per JSON chunk.
- First/last records and chunk-boundary records.

The parser was run on **1,022 / 11,000 records (9.29%)**. It did not parse the remaining 9,978 records. Structural feature discovery scanned their JSON fields to select representative cases; it did not include their text in the parsed sample.

## Results

- **1,022 / 1,022** sampled records passed exact verification against their original JSON records.
- Event IDs were unique; the parsed sample was chronologically ordered after the parser's source-aware merge.
- Sender, raw timestamp, raw content, attachment references, reactions, share/call fields and remaining platform metadata matched the original source records.
- Timestamp conversion matched the test timezone for all sampled records. This is a technical test, not confirmation of the user's historical timezone.
- 125 sampled records contained 129 attachment-reference occurrences.
- 126 references linked to 126 distinct supplied media assets; three video references remain missing.
- All 126 supplied assets had SHA-256 hashes. No unsafe reference or orphaned supplied asset was found.
- Sample event kinds: 529 text, 297 share, 102 photo, 34 reaction, 16 audio, 13 call, 8 system, 7 video and 16 unknown.
- 594 sampled strings were classified as mojibake candidates and passed the guarded repair path. 166 actual display-value changes were independently checked; zero transform mismatches occurred. Raw values remain preserved separately.

## Attachment and media edge cases

The export contains 126 supplied assets: 106 photos, 15 audio files, one MP4 container used by an `audio_files` reference, and four videos.

One audio reference points to an MP4 container. Optional `ffprobe` found one AAC audio stream and no video stream, with duration approximately 7.57 seconds. The correct presentation role is therefore **audio**, while the container MIME remains `video/mp4`. The parser must preserve both facts and must not infer the playback role from extension alone.

Three video references have no corresponding supplied file. They remain `referenced-but-missing`; no replacement is guessed. The 126 supplied assets are all linked by exact safe relative URI and none is orphaned in this sample.

## Edge cases covered

| Edge case | Result |
|---|---|
| Photos, videos, audio and multiple attachments | All 125 attachment-bearing records included |
| Missing video references | Three explicitly missing |
| Partial share objects with optional fields absent | Preserved and exact-verified |
| Multiple reactions on one record | Preserved and exact-verified |
| Call duration zero | Synthetic regression passes |
| Null/empty content with other event metadata | Preserved as records |
| Chunk order and cross-chunk boundary | Both chunks newest-first; source indices retained |
| Mojibake candidates mixed with valid Unicode | Guarded repair; raw and display values separate |
| `is_unsent_image_by_messenger_kid_parent` | Preserved as metadata; not treated as deletion proof |
| Same-named `message_1.json` across conversations | Synthetic event-ID collision regression passes |
| ZIP directory entries and unsafe paths | Standard directory entries accepted; traversal/collision rejected |

## Limits

- The test timezone was `Asia/Kolkata` for timestamp conversion only. The user's actual historical timezone still needs confirmation.
- Media files were inventoried, signature-checked, hashed and linked; personal images/audio/video were not viewed or listened to.
- Three referenced video files are absent from the export.
- The test validates 1,022 carefully selected records, not all 11,000. Full ingestion remains necessary for the final webpage and must run with chunked processing and full line/record accounting.
- A bounded parser test cannot prove that every unselected record is free of unusual structures. The selection includes all attachment/call records and broad edge-case coverage, but unexpected unseen schema variants remain possible.

## Decision

The expanded real-export test passes. It materially strengthens Instagram coverage without processing the entire message history. The skill now accepts the original ZIP directly for this regression test, safely extracts it to a temporary directory, and removes the temporary extraction afterward. The remaining work before webpage generation is full, checkpointed ingestion after the user confirms the timezone and reviews the missing-media report.

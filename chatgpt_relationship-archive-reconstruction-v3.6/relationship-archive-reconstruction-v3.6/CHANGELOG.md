# Changelog

## 3.6.0 — Expanded Instagram real-export regression

- Increased the real Instagram regression sample from 692 to 1,022 records (9.29% of the 11,000-record export).
- Kept all 125 attachment-bearing records, all 13 call records, all multi-attachment and share-plus-reaction combinations; increased stratified reaction/share/notice/empty/mojibake coverage, uniform timeline coverage and deterministic random sampling.
- Re-ran exact source-record verification: 1,022/1,022 pass, including sender, timestamp, raw content, attachments, reactions, shares, calls, platform metadata and test-timezone conversion.
- Re-verified all 126 supplied Instagram assets: 126 linked, zero unsafe references, zero orphaned assets, three missing video references explicitly retained.
- Added direct ZIP input support to the stratified regression runner; it safely extracts to a temporary directory and cleans up afterward.
- Updated the aggregate-only Instagram regression report and versioned package documentation.


## 3.4.0 — WhatsApp/Instagram combined export support
- Added safe export ZIP handling, media asset inventory and source-linked audit tools.
- Added Instagram audio MP4 container-role separation and exact URI linking.

## 3.3.0 and earlier
See previous package changelog history where available. This release carries forward the evidence-first, source-faithful, privacy-first and model-portable intent.

# Test evidence

Run from the package root:

```bash
python3 tools/chat_tools.py --selftest
python3 tools/chat_tools.py --parity  # Node.js required
python3 tools/media_tools.py --selftest
python3 tests/test_resume_handoff.py
python3 tests/test_instagram_stratified_sample.py /path/to/instagram-export.zip --timezone Asia/Kolkata
```

`real-export-results.json` records the earlier combined real-export audit. `instagram-stratified-results.json` records the expanded targeted sample. Both are aggregate-only and exclude message bodies, participant names and media filenames.

The 1,022-message Instagram regression sample is not the final archive ingestion. It is a targeted parser test created after a structural scan of 11,000 source records. All attachment-bearing messages and call records were included; other edge cases were sampled by feature, chronology and deterministic random selection. 9,978 non-selected array slots were replaced with null placeholders only in a temporary sparse test fixture to preserve original record indices; the original source contained zero non-dictionary records.

Actual image/audio/video contents were not interpreted. Technical stream metadata was probed only for the MP4 stored under `audio_files`; it contained AAC audio only. Provider token/session expiry remains Not tested at provider level; handoff and interrupted-chunk recovery are simulated with files/checksums.

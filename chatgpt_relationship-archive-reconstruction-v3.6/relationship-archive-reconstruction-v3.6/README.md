# Chat Story Webpage — Relationship Archive Reconstruction v3.6.0

A portable Agent Skill for creating a private, intimate and source-traceable archive from WhatsApp and Instagram conversations, including supplied personal media. It combines human-centred reading rules, evidence-backed outside analysis, a complete chat reader, first-class media preservation and cross-session/model continuity.

## Start here

1. Read `SKILL.md` and all files in `references/`.
2. Keep `tools/`, `tests/` and `templates/` with the skill.
3. Upload the skill and original exports. For WhatsApp, a text-only export can be the primary chronology and a with-media export can act as a companion for original attachments. For Instagram, include the JSON export and referenced media folder/ZIP.
4. Ask the AI to perform Pass 1 (inventory, parsing audit and media inventory) only. Review the report before analysis or webpage design.
5. Keep the project workspace, original assets, manifest and checkpoints outside chat history.

## Local tests

```bash
python3 tools/chat_tools.py --selftest
python3 tools/chat_tools.py --parity       # requires Node.js
python3 tools/media_tools.py --selftest
python3 tests/test_resume_handoff.py
python3 tests/test_instagram_stratified_sample.py /path/to/instagram-export.zip --timezone Asia/Kolkata
python3 tools/audit_exports.py /path/to/whatsapp.zip /path/to/instagram.zip --whatsapp-senders 'Person A|Person B' --instagram-timezone Asia/Kolkata --output audit.json
```

The Instagram sample test accepts either the original ZIP or an extracted export. For ZIP input it uses safe temporary extraction, scans the message JSON structure to locate feature edge cases, then parses a deterministic sample while preserving original message indices. It is a regression test, not a replacement for the full parse used to build the final archive.

## Privacy and media

Private relationship conversation and supplied personal media are included by default unless the user excludes specific items. Sensitive/intimate media may have an optional reveal control, but is not silently removed. Original bytes are preserved and hashed. Unknown media remains available for review. Security secrets (passwords, OTPs, API keys, tokens, cookies and recovery codes) are never included.

The test reports in `tests/` are aggregate-only. They do not include message bodies, participant names, original media filenames or the source exports.

## Cross-session continuity

Use `templates/resume-prompt.md` and `references/project-continuity-and-handoff.md`. Level A is status/code only. Level B is the recommended handoff for content-dependent continuation after explicit approval of the receiving service and selected normalized data/media. Level C transfers originals only when raw reprocessing is needed. Never transfer credentials.

# Project Continuity and Cross-Model Handoff Protocol

This protocol is mandatory. The project must survive context/token limits, session expiry, browser closure, account switching, model/provider changes and temporary execution-environment resets. Chat history is not the project database.

## 1. Portable workspace

```text
story-project/
  README.md
  PROJECT-STATUS.md
  project-manifest.json
  state/project-state.json
  state/checkpoints/CP-000001.json + CP-000001.md
  logs/operations.jsonl
  logs/decisions.jsonl
  data/source/          untouched exports (private)
  data/normalized/      validated source chunks (.jsonl)
  data/media/           original supplied media bytes (unchanged)
  data/derived-media/   thumbnails, transcripts, waveforms (derivatives only)
  data/media-manifest.json
  analysis/              outline, glossary, evidence cards, open questions
  app/                   portable code, assets, lockfile, build instructions
  tests/                 parser, media, security, UI and handoff tests
  reports/               audit, QA, handoff and completion reports
```

Use relative paths. Never make `/mnt/data/...`, a provider-specific canvas, cloud preview or hidden memory the only reference to an artifact.

## 2. Required state artifacts

`PROJECT-STATUS.md` must state current phase, last verified checkpoint, completed/partial/not-started work, exact next action, open decisions, blockers, files required next and latest test status.

`project-manifest.json` lists every important artifact with relative path, role, size, SHA-256, source/platform, date coverage, schema/parser version, availability status, sensitivity and handoff eligibility. Media records additionally carry asset ID, category, MIME, hash, linked event IDs and playback status.

`state/project-state.json` records current phase, last verified operation/checkpoint, completed work units, next unprocessed locator, pending decisions, tool assumptions and media coverage.

`logs/operations.jsonl` and `logs/decisions.jsonl` are append-only. Corrections/reversals are new records, not edits that erase history. Do not log raw message text or credentials.

Every numbered checkpoint has JSON and human-readable Markdown forms. Include exact next action, source coverage, output paths/hashes, media-manifest hash/counts, blockers, pending decisions and interruption state. A chat summary alone is not a checkpoint.

## 3. Checkpoint triggers and transaction

Checkpoint after initial inventory, each source file/parse chunk, media inventory/linking, timezone/identity decisions, data-health report, every user correction/approval, each analysis gate, each major app feature, QA, packaging, and before a likely session/token cutoff or model/account switch.

For each bounded work unit:
1. Write to a temporary output.
2. Reopen and validate schema, counts, source locators and hash.
3. Atomically rename it to its final path where supported.
4. Append the operation log, update manifest/state, then write a numbered checkpoint and status file.
5. Confirm status/state/checkpoint/manifest agree.

An interrupted `.tmp` output is unverified. Quarantine it and resume from the last verified locator. Deterministic event/chunk IDs and idempotent operations prevent duplicate records on retry.

## 4. Handoff levels

**Level A — Status/code only (default when no transfer scope is selected).** Includes skill, status, decisions, checkpoints, app source, tests and aggregate media metadata. Excludes raw exports, normalized message text and media bytes. It is enough for project management/app development, not content-dependent analysis or media playback.

**Level B — Working-data handoff (recommended for content-dependent continuation).** May include user-selected normalized conversation chunks, media manifest, selected original media bytes, reviewed analysis and app source. It can contain the entire private conversation. Create it only after the user approves the receiving service/account and the exact paths/categories being transferred. For analysis plus rendering, include both the normalized event data and the referenced media bytes; a manifest alone cannot restore playback.

**Level C — Full-source handoff.** Original exports and companion media, only when raw re-parsing/forensic verification is needed and after explicit approval of the receiving service/account and scope.

Never include API keys, access/refresh tokens, cookies, passwords, private keys or recovery codes at any level. Re-authentication happens through the destination provider's secure flow.

Every handoff ZIP includes a manifest of included/excluded files, sizes, hashes, sensitivity, media IDs and purpose. Verify the ZIP opens and all copied hashes match after extraction. A manifest entry is not a substitute for file bytes.

## 5. Account/session/model switch recovery

A new AI must:
1. Read `SKILL.md`, all references, README, PROJECT-STATUS, manifest, state, latest checkpoint and logs.
2. Verify hashes and existence of required files, including normalized chunks and each media asset needed for the next action.
3. Check which original exports/media are actually present in the new environment. Never assume another account can see prior attachments, memory, connected apps, tools or generated files.
4. Inspect its own tools/runtime and declare capability gaps.
5. Re-run only minimum integrity/smoke checks; do not repeat validated work unless an integrity check fails.
6. Preserve stable event IDs, schema versions, user decisions and app architecture.
7. Resume from the exact next unprocessed locator and save a new checkpoint before further substantial work.

If status, state, manifest and checkpoint disagree, stop and report. If no valid checkpoint exists, enter recovery mode and mark anything not proven by files/logs as unverified.

## 6. Resume prompt

Use `templates/resume-prompt.md`. The receiving AI must report what is verified, missing, partial and next before continuing. It must not ask the user to repeat decisions already present in the decision log.

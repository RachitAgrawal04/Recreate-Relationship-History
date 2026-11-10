# Relationship Archive Project

## Purpose
A private, source-faithful reconstruction of supplied WhatsApp and Instagram conversations and media.

## Versioning
- Skill version:
- Project schema version:
- Normalized event schema version:
- Parser versions:
- App version:

## Workspace
- `data/source/`: untouched exports (restricted/private).
- `data/normalized/`: validated events, source chunks.
- `data/media/`: original supplied media bytes.
- `data/derived-media/`: thumbnails, waveforms, transcripts and other derivatives.
- `data/media-manifest.json`: inventory, hashes, links and statuses.
- `analysis/`: outline, glossary, evidence cards and open questions.
- `app/`: portable app source, assets, lockfiles and instructions.
- `state/`, `checkpoints/`, `logs/`: project recovery state.
- `tests/`, `reports/`: validation and QA evidence.

## Resume
Read `PROJECT-STATUS.md`, the manifest, project state, latest checkpoint and logs; verify hashes before continuing. Use `templates/resume-prompt.md` from the skill package.

## Run/test
- Runtime/toolchain:
- Install command:
- Development command:
- Build command:
- Test command:

## Privacy
- Default delivery: local/private.
- Private relationship conversations and supplied media: preserved by default unless the user excludes them.
- Security secrets: never included.
- Handoff level and approved scope:

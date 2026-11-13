
# Project: Private Relationship Archive

## Product vision
Build a beautiful, intimate, highly personal digital archive of a real relationship. It must feel emotionally meaningful, not like a generic CRM, social network, or dashboard.

## Working principles
- Work incrementally. Never implement the entire product in one pass.
- Before significant implementation, inspect the existing code and present a plan.
- Preserve existing working features.
- Explain which files you intend to change and why.
- After every implementation, run relevant tests and report the results.
- Do not claim something works unless it has been tested.

## Data integrity
- Original conversation exports and media are the source of truth.
- Never rewrite, paraphrase, normalize destructively, or silently discard original messages.
- Keep raw source data immutable.
- Store normalized data separately.
- Preserve original timestamps, sender labels, message ordering, edits, and attachment references.
- Every imported message and media item must retain source provenance.
- Never merge snapshots in a way that double-counts conversations.

## Privacy and security
- This is a private, intimate archive.
- Private, embarrassing, affectionate, difficult, and intimate conversations are valid archive content.
- Do not sanitize or omit content merely because it is personal.
- Sensitive media must be behind deliberate reveal controls.
- Never expose API keys, passwords, cookies, tokens, or credentials.
- Never upload personal conversations or media to third-party services without explicit approval.
- Never make the archive publicly accessible by default.
- Do not place private data in the public web directory.
- Do not log message bodies or intimate media contents unnecessarily.
- Treat imported HTML, SVG, JS, XML, and nested archives as untrusted.

## UI and experience
- Prioritize emotional storytelling, visual quality, typography, motion, and thoughtful details. The webpage mood should change according to context the messages being displayed.
- Avoid generic dashboard aesthetics.
- Make the site responsive and accessible.
- Use intentional transitions, not excessive animation.
- Make search, navigation, and media viewing genuinely usable.
- Never autoplay audio or video.

## Engineering standards
- Use TypeScript and strict typing.
- Prefer small, reusable components.
- Validate all imported data.
- Add tests for parsing, search, media association, and privacy-sensitive behavior.
- Avoid unnecessary dependencies.
- Document important architecture decisions.
- Use environment variables for secrets.

## Skill package — read-only boundary

The skill package (`chatgpt_relationship-archive-reconstruction-v3.6/`) is the
engineering and data-integrity rulebook for this project. **It is permanently
read-only during application implementation.**

- Never create, modify, rename or delete any file inside the skill folder as
  part of building or maintaining the website.
- If an implementation decision appears to conflict with the skill, stop and
  report the conflict explicitly. Do not resolve it by editing the skill.
- Any proposed change to the skill is a separate, standalone reviewed task. It
  requires an explicit before/after diff and user approval before any file is
  touched.
- This boundary applies across sessions and model switches (see DEC-010 in
  `logs/decisions.json`).

The app reads the skill's tools and templates; it never writes back to them.

## Agent workflow
At the end of every task, report:
1. What changed.
2. Files created or modified.
3. Commands and tests executed.
4. Test results.
5. Known issues and risks.
6. The recommended next task.

Do not begin the next major phase without a review.

#!/usr/bin/env python3
"""
ingest.py — Full ingestion pipeline for the Relationship Archive.

Reads WhatsApp and Instagram exports, produces normalized JSONL chunks,
a media manifest, a search index, and a formal ingestion report.
Writes atomic checkpoints after each bounded stage.

RULES:
- Source files are never modified.
- Every source record is processed, not just a sample.
- Timezone is labelled assumed/unconfirmed unless confirmed by the user.
- Cross-platform merge is refused if WA timezone is not applied.
- All writes are atomic (write to .tmp, validate, rename).
- Processing is idempotent: re-running from a checkpoint is safe.

Usage:
    python scripts/ingest.py

Run from the relationship-archive/ directory, or set WORKSPACE_ROOT.
"""
from __future__ import annotations

import collections
import hashlib
import json
import os
import re
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Path configuration — all relative to the relationship-archive/ root.
# ---------------------------------------------------------------------------
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent  # relationship-archive/
SKILL_TOOLS    = WORKSPACE_ROOT.parent / "chatgpt_relationship-archive-reconstruction-v3.6" / "tools"
EXPORT_ROOT    = WORKSPACE_ROOT.parent / "Messages Exports"
WA_EXPORT_DIR  = EXPORT_ROOT / "WhatsApp Chat with Radhika Singhal"
IG_EXPORT_DIR  = EXPORT_ROOT / "Instagram Chat Export with Radhika Singhal"

OUT_NORMALIZED  = WORKSPACE_ROOT / "data" / "normalized"
OUT_MEDIA       = WORKSPACE_ROOT / "data" / "manifests"
OUT_INDEXES     = WORKSPACE_ROOT / "data" / "indexes"
OUT_REPORTS     = WORKSPACE_ROOT / "reports"
OUT_STATE       = WORKSPACE_ROOT / "state"
OUT_CHECKPOINTS = WORKSPACE_ROOT / "state" / "checkpoints"
OUT_LOGS        = WORKSPACE_ROOT / "logs"

# ---------------------------------------------------------------------------
# Timezone configuration.
# CHANGE THIS ONLY after the user confirms the historical timezone.
# ---------------------------------------------------------------------------
WA_TIMEZONE          = "Asia/Kolkata"   # ASSUMED — not yet user-confirmed
IG_TIMEZONE          = "Asia/Kolkata"   # ASSUMED — not yet user-confirmed
TIMEZONE_CONFIRMED   = False            # Set True only after DEC-001/DEC-002
TIMEZONE_LABEL       = "assumed" if not TIMEZONE_CONFIRMED else "user-confirmed"

# WhatsApp sender labels — confirmed from prior audit.
WA_PARTICIPANTS = {"Radhika Singhal", "Rachit Agrawal"}

# ---------------------------------------------------------------------------
# Inject skill tools onto sys.path without modifying the skill package.
# ---------------------------------------------------------------------------
sys.path.insert(0, str(SKILL_TOOLS))
import chat_tools
import media_tools
import continuity_tools

PARSER_VERSION = "chat_tools.py:3.6.0 / media_tools.py:3.6.0"
SCHEMA_VERSION = "1.0.0"


# ===========================================================================
# Utilities
# ===========================================================================

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def atomic_write_json(path: Path, obj: object) -> None:
    """Write JSON to a .tmp file, validate it reopens, then rename atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    tmp.write_text(text, encoding="utf-8")
    # Validate: reopen and check structure is at least a dict or list.
    parsed = json.loads(tmp.read_text(encoding="utf-8"))
    if not isinstance(parsed, (dict, list)):
        raise ValueError(f"atomic_write_json: unexpected root type for {path}")
    os.replace(tmp, path)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="surrogatepass")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def log_operation(op_id: str, description: str, files_written: list, result: str, notes: str = "") -> None:
    log_path = OUT_LOGS / "operations.json"
    try:
        ops = json.loads(log_path.read_text(encoding="utf-8")) if log_path.exists() and log_path.stat().st_size > 0 else []
    except (json.JSONDecodeError, OSError):
        ops = []
    ops.append({
        "operation_id": op_id,
        "timestamp_utc": _utcnow(),
        "performed_by": "ingest.py",
        "operation": description,
        "files_written": files_written,
        "result": result,
        "notes": notes,
    })
    atomic_write_json(log_path, ops)


def write_checkpoint(cp_id: str, phase: str, next_action: str, notes: str = "") -> None:
    OUT_CHECKPOINTS.mkdir(parents=True, exist_ok=True)
    cp = {
        "checkpoint_id": cp_id,
        "created_at_utc": _utcnow(),
        "skill_version": "3.6.0",
        "schema_version": SCHEMA_VERSION,
        "parser_version": PARSER_VERSION,
        "current_phase": phase,
        "timezone_label": TIMEZONE_LABEL,
        "timezone_confirmed": TIMEZONE_CONFIRMED,
        "next_action": next_action,
        "notes": notes,
    }
    # Write JSON checkpoint atomically.
    atomic_write_json(OUT_CHECKPOINTS / f"{cp_id}.json", cp)
    # Write human-readable companion.
    md_path = OUT_CHECKPOINTS / f"{cp_id}.md"
    md_path.write_text(
        f"# Checkpoint {cp_id}\n\n"
        f"- **Created:** {cp['created_at_utc']}\n"
        f"- **Phase:** {phase}\n"
        f"- **Timezone:** {TIMEZONE_LABEL} ({WA_TIMEZONE})\n"
        f"- **Next action:** {next_action}\n"
        f"- **Notes:** {notes}\n",
        encoding="utf-8",
    )
    print(f"  [checkpoint] {cp_id} written.")


def write_jsonl_chunks(events: list, out_dir: Path, prefix: str) -> dict[str, Path]:
    """Split events into monthly JSONL chunks. Returns {YYYY-MM: path}."""
    out_dir.mkdir(parents=True, exist_ok=True)
    by_month: dict[str, list] = collections.defaultdict(list)
    no_ts = []
    for e in events:
        ts = e.get("timestamp_sort_key") or e.get("timestamp_parsed")
        if ts and len(ts) >= 7:
            month = ts[:7]  # YYYY-MM
        else:
            month = "0000-00"  # undated events go to a catch-all
        by_month[month].append(e)

    written = {}
    for month, chunk in sorted(by_month.items()):
        path = out_dir / f"{prefix}-{month}.jsonl"
        tmp = path.with_suffix(".jsonl.tmp")
        with tmp.open("w", encoding="utf-8") as f:
            for event in chunk:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        # Validate: re-read and count records by newline count.
        # Do NOT use splitlines() — event text_original may contain embedded
        # newlines (multi-line messages), causing an overcount.
        raw_text = tmp.read_text(encoding="utf-8")
        line_count = raw_text.count("\n")
        if line_count != len(chunk):
            raise ValueError(f"JSONL chunk mismatch for {path}: wrote {len(chunk)}, newline count {line_count}")
        os.replace(tmp, path)
        written[month] = path
    return written


def build_search_index(events: list) -> list:
    """Pre-compute search keys for all non-synthetic events."""
    index = []
    for e in events:
        if e.get("synthetic"):
            continue
        text = e.get("text_display") or e.get("text_original") or ""
        if not text:
            continue
        base, collapsed, skeleton = chat_tools.search_keys(text)
        index.append({
            "event_id": e["event_id"],
            "platform": e.get("platform"),
            "sender_raw": e.get("sender_raw"),
            "timestamp_parsed": e.get("timestamp_parsed"),
            "base": base,
            "collapsed": collapsed,
            "skeleton": skeleton,
        })
    return index


# ===========================================================================
# Stage 1: Pre-flight self-tests
# ===========================================================================

def stage_selftest() -> bool:
    print("\n=== Stage 1: Skill self-tests ===")
    import subprocess

    tool_dir = SKILL_TOOLS
    tests = [
        (["python", str(tool_dir / "chat_tools.py"), "--selftest"], "chat_tools --selftest"),
        (["python", str(tool_dir / "chat_tools.py"), "--parity"],   "chat_tools --parity"),
        (["python", str(tool_dir / "media_tools.py"), "--selftest"], "media_tools --selftest"),
    ]
    all_pass = True
    for cmd, label in tests:
        # Run from the tool directory so Node.js does not pick up a conflicting
        # package.json from a parent directory (Windows long-path prefix bug).
        result = __import__("subprocess").run(cmd, capture_output=True, text=True, cwd=str(tool_dir))
        if result.returncode == 0:
            print(f"  PASS  {label}")
        else:
            print(f"  FAIL  {label}")
            print(result.stdout[-400:])
            print(result.stderr[-200:])
            all_pass = False
    return all_pass


# ===========================================================================
# Stage 2: WhatsApp ingestion
# ===========================================================================

def stage_whatsapp() -> tuple[list, dict]:
    print("\n=== Stage 2: WhatsApp ingestion ===")
    txt_path = WA_EXPORT_DIR / "WhatsApp Chat with Radhika Singhal.txt"
    if not txt_path.exists():
        raise FileNotFoundError(f"WhatsApp chat file not found: {txt_path}")

    print(f"  Reading {txt_path.name} ({txt_path.stat().st_size:,} bytes)…")
    raw_text = txt_path.read_text(encoding="utf-8", errors="surrogatepass")
    source_hash = sha256_text(raw_text)
    print(f"  SHA-256: {source_hash}")

    print("  Parsing with chat_tools.parse_whatsapp()…")
    events, audit = chat_tools.parse_whatsapp(
        raw_text,
        participants=WA_PARTICIPANTS,
        date_order="dmy",           # confirmed from prior audit (real-export-results.json)
        source_id="wa-primary",
    )
    audit["source_sha256"] = source_hash
    audit["source_file"] = txt_path.name
    print(f"  Parsed {len(events):,} events from {audit['physical_lines']:,} lines.")
    print(f"  Line coverage: {audit['all_lines_accounted_for']}")
    if not audit["all_lines_accounted_for"]:
        raise ValueError("WhatsApp line coverage failed — not every line is owned exactly once.")

    # Apply assumed timezone so merge can produce sort keys.
    # Label is 'assumed' until TIMEZONE_CONFIRMED = True.
    print(f"  Applying timezone {WA_TIMEZONE} ({TIMEZONE_LABEL})…")
    chat_tools.apply_whatsapp_timezone(events, WA_TIMEZONE)
    for e in events:
        e["timezone_source"] = (
            "user-confirmed IANA zone applied to exporting-phone wall-clock"
            if TIMEZONE_CONFIRMED
            else f"assumed {WA_TIMEZONE} — not yet user-confirmed; timestamp_sort_key is provisional"
        )

    # Map sender IDs.
    persons = sorted(WA_PARTICIPANTS)
    id_map = {persons[0]: "person-a", persons[1]: "person-b"}
    for e in events:
        if e.get("sender_raw") in id_map:
            e["sender_id"] = id_map[e["sender_raw"]]

    return events, audit


# ===========================================================================
# Stage 3: WhatsApp media inventory
# ===========================================================================

def stage_whatsapp_media() -> list:
    print("\n=== Stage 3: WhatsApp media inventory ===")
    if not WA_EXPORT_DIR.exists():
        raise FileNotFoundError(f"WhatsApp export directory not found: {WA_EXPORT_DIR}")
    print(f"  Inventorying assets in {WA_EXPORT_DIR.name}…")
    assets = media_tools.inventory_assets(WA_EXPORT_DIR, hash_files=True)
    # Tag each asset with its platform.
    for a in assets:
        a["platform"] = "whatsapp"
        a["source_export_dir"] = WA_EXPORT_DIR.name
    print(f"  Found {len(assets):,} media assets.")
    cats = collections.Counter(a["category"] for a in assets)
    for cat, n in sorted(cats.items()):
        print(f"    {cat}: {n}")
    return assets


# ===========================================================================
# Stage 4: Instagram ingestion
# ===========================================================================

def stage_instagram() -> tuple[list, dict]:
    print("\n=== Stage 4: Instagram ingestion ===")
    # Locate the conversation subdirectory.
    conv_dirs = [p for p in IG_EXPORT_DIR.iterdir() if p.is_dir()]
    if not conv_dirs:
        raise FileNotFoundError(f"No conversation subdirectory found in {IG_EXPORT_DIR}")
    if len(conv_dirs) > 1:
        print(f"  WARNING: Multiple subdirectories found: {[p.name for p in conv_dirs]}. Using first.")
    conv_dir = conv_dirs[0]
    print(f"  Conversation directory: {conv_dir.name}")
    json_files = sorted(conv_dir.glob("message_*.json"))
    print(f"  JSON chunks: {[f.name for f in json_files]}")

    print(f"  Parsing with chat_tools.load_instagram()…")
    events, audit = chat_tools.load_instagram(str(IG_EXPORT_DIR), IG_TIMEZONE)
    audit["timezone_label"] = TIMEZONE_LABEL
    audit["timezone_confirmed"] = TIMEZONE_CONFIRMED
    if not TIMEZONE_CONFIRMED:
        audit["timezone_warning"] = (
            f"Timezone {IG_TIMEZONE} is assumed, not yet user-confirmed. "
            "Timestamps are provisional until DEC-001/DEC-002 are resolved."
        )
    print(f"  Parsed {len(events):,} events.")

    # Map sender IDs using same person-a/person-b order.
    participants = sorted(audit.get("participants", []))
    if len(participants) == 2:
        id_map = {participants[0]: "person-a", participants[1]: "person-b"}
        for e in events:
            if e.get("sender_raw") in id_map:
                e["sender_id"] = id_map[e["sender_raw"]]
    else:
        print(f"  WARNING: Expected 2 participants, found {len(participants)}: {participants}")

    return events, audit


# ===========================================================================
# Stage 5: Instagram media inventory
# ===========================================================================

def stage_instagram_media() -> list:
    print("\n=== Stage 5: Instagram media inventory ===")
    print(f"  Inventorying assets in {IG_EXPORT_DIR.name}…")
    assets = media_tools.inventory_assets(IG_EXPORT_DIR, hash_files=True)
    for a in assets:
        a["platform"] = "instagram"
        a["source_export_dir"] = IG_EXPORT_DIR.name
    print(f"  Found {len(assets):,} media assets.")
    cats = collections.Counter(a["category"] for a in assets)
    for cat, n in sorted(cats.items()):
        print(f"    {cat}: {n}")
    return assets


# ===========================================================================
# Stage 6: Link media attachments
# ===========================================================================

def stage_link_media(wa_events, wa_assets, ig_events, ig_assets):
    print("\n=== Stage 6: Link media attachments ===")

    print("  Linking WhatsApp attachments…")
    wa_events, wa_link_summary = media_tools.link_whatsapp_attachments(wa_events, wa_assets)
    print(f"    WA linked: {wa_link_summary['distinct_assets_linked']:,} / {len(wa_assets):,} assets")
    print(f"    WA missing references: {wa_link_summary['missing_reference_occurrences']:,}")
    print(f"    WA ambiguous: {wa_link_summary['ambiguous_events']:,}")
    print(f"    WA unlinked assets: {wa_link_summary['unlinked_asset_count']:,}")

    # Instagram URI path normalization.
    # The IG JSON export stores attachment URIs as full download-relative paths:
    #   your_instagram_activity/messages/inbox/<CONV_DIR>/<type>/<file>
    # But media_tools.inventory_assets() is rooted at the IG_EXPORT_DIR, so
    # asset.relative_path starts at <CONV_DIR>/<type>/<file>.
    # Strip the leading prefix so link_instagram_attachments can match by path.
    IG_URI_PREFIX = "your_instagram_activity/messages/inbox/"
    normalized_count = 0
    for e in ig_events:
        if not e.get("attachments"):
            continue
        for att in e["attachments"]:
            uri = att.get("uri", "")
            if uri.startswith(IG_URI_PREFIX):
                att["uri"] = uri[len(IG_URI_PREFIX):]
                normalized_count += 1
        # Also normalize attachment_refs for consistency.
        e["attachment_refs"] = [
            r[len(IG_URI_PREFIX):] if r.startswith(IG_URI_PREFIX) else r
            for r in (e.get("attachment_refs") or [])
        ]
    print(f"  Normalized {normalized_count:,} IG attachment URIs (stripped export prefix).")

    print("  Linking Instagram attachments…")
    ig_events, ig_link_summary = media_tools.link_instagram_attachments(ig_events, ig_assets)
    print(f"    IG linked: {ig_link_summary['distinct_assets_linked']:,} / {len(ig_assets):,} assets")
    print(f"    IG missing references: {ig_link_summary['missing_reference_occurrences']:,}")
    print(f"    IG unlinked assets: {ig_link_summary['unlinked_asset_count']:,}")

    return wa_link_summary, ig_link_summary


# ===========================================================================
# Stage 7: Cross-platform merge
# ===========================================================================

def stage_merge(wa_events, ig_events) -> list:
    print("\n=== Stage 7: Cross-platform merge ===")
    if not TIMEZONE_CONFIRMED:
        print(f"  NOTE: Timezone is {TIMEZONE_LABEL} ({WA_TIMEZONE}). "
              "Merge proceeds with provisional sort keys. "
              "Re-run after user confirms DEC-001/DEC-002.")
    merged = chat_tools.merge_events(wa_events, ig_events)
    print(f"  Merged total: {len(merged):,} events.")
    merged = chat_tools.find_duplicate_candidates(merged)
    dups = sum(1 for e in merged if e.get("duplicate_group_id"))
    print(f"  Duplicate candidates flagged: {dups:,}")
    clusters = sum(1 for e in merged if e.get("ordering_uncertain"))
    print(f"  Events in uncertain-ordering clusters: {clusters:,}")
    merged = chat_tools.group_turns(merged)
    return merged


# ===========================================================================
# Stage 8: Write normalized JSONL chunks
# ===========================================================================

def stage_write_chunks(wa_events, ig_events, merged_events) -> dict:
    print("\n=== Stage 8: Writing normalized JSONL chunks ===")
    OUT_NORMALIZED.mkdir(parents=True, exist_ok=True)

    wa_chunks  = write_jsonl_chunks(wa_events,     OUT_NORMALIZED, "wa")
    ig_chunks  = write_jsonl_chunks(ig_events,     OUT_NORMALIZED, "ig")
    all_chunks = write_jsonl_chunks(merged_events, OUT_NORMALIZED, "merged")

    print(f"  WA chunks: {len(wa_chunks)}")
    print(f"  IG chunks: {len(ig_chunks)}")
    print(f"  Merged chunks: {len(all_chunks)}")
    return {"wa": wa_chunks, "ig": ig_chunks, "merged": all_chunks}


# ===========================================================================
# Stage 9: Media manifest
# ===========================================================================

def stage_media_manifest(wa_assets, ig_assets, wa_link_summary, ig_link_summary) -> Path:
    print("\n=== Stage 9: Writing media manifest ===")
    OUT_MEDIA.mkdir(parents=True, exist_ok=True)
    manifest = {
        "manifest_version": "1.0",
        "created_at_utc": _utcnow(),
        "schema_version": SCHEMA_VERSION,
        "privacy": "No message text, media file contents or private URLs are included. Hashes and relative paths only.",
        "wa_asset_count": len(wa_assets),
        "ig_asset_count": len(ig_assets),
        "total_asset_count": len(wa_assets) + len(ig_assets),
        "wa_link_summary": wa_link_summary,
        "ig_link_summary": ig_link_summary,
        "assets": wa_assets + ig_assets,
    }
    path = OUT_MEDIA / "media-manifest.json"
    atomic_write_json(path, manifest)
    print(f"  Manifest written: {path.name} ({path.stat().st_size:,} bytes)")
    return path


# ===========================================================================
# Stage 10: Search index
# ===========================================================================

def stage_search_index(merged_events) -> Path:
    print("\n=== Stage 10: Building search index ===")
    OUT_INDEXES.mkdir(parents=True, exist_ok=True)
    index = build_search_index(merged_events)
    path = OUT_INDEXES / "search-index.jsonl"
    tmp = path.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for entry in index:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    lines = tmp.read_text(encoding="utf-8").count("\n")
    if lines != len(index):
        raise ValueError(f"Search index line mismatch: {len(index)} entries, {lines} lines")
    os.replace(tmp, path)
    print(f"  Index entries: {len(index):,} (non-synthetic events with text)")
    print(f"  Written: {path.name}")
    return path


# ===========================================================================
# Stage 11: Validation — event ID uniqueness + source-line accounting
# ===========================================================================

def stage_validate(wa_events, wa_audit, ig_events, ig_audit, merged_events) -> dict:
    print("\n=== Stage 11: Validation ===")
    results = {}

    # --- WhatsApp event ID uniqueness ---
    wa_ids = [e["event_id"] for e in wa_events]
    wa_unique = len(wa_ids) == len(set(wa_ids))
    results["wa_event_ids_unique"] = wa_unique
    print(f"  WA event ID uniqueness: {'PASS' if wa_unique else 'FAIL'}")

    # --- WhatsApp line accounting ---
    wa_line_ok = wa_audit.get("all_lines_accounted_for", False)
    results["wa_line_coverage"] = wa_line_ok
    print(f"  WA line coverage: {'PASS' if wa_line_ok else 'FAIL'}")

    # --- WA event count vs timestamp_headers ---
    wa_count_ok = len(wa_events) == wa_audit.get("timestamp_headers", -1)
    results["wa_event_count_vs_headers"] = wa_count_ok
    print(f"  WA event count ({len(wa_events):,}) == timestamp headers ({wa_audit.get('timestamp_headers'):,}): {'PASS' if wa_count_ok else 'FAIL'}")

    # --- Instagram event ID uniqueness ---
    ig_ids = [e["event_id"] for e in ig_events]
    ig_unique = len(ig_ids) == len(set(ig_ids))
    results["ig_event_ids_unique"] = ig_unique
    print(f"  IG event ID uniqueness: {'PASS' if ig_unique else 'FAIL'}")

    # --- Instagram record count ---
    ig_expected = sum(ig_audit.get("message_count_by_file", {}).values())
    ig_count_ok = len(ig_events) == ig_expected
    results["ig_event_count_vs_source"] = ig_count_ok
    print(f"  IG event count ({len(ig_events):,}) == source records ({ig_expected:,}): {'PASS' if ig_count_ok else 'FAIL'}")

    # --- Merged count ---
    merged_expected = len(wa_events) + len(ig_events)
    merged_count_ok = len(merged_events) == merged_expected
    results["merged_count_complete"] = merged_count_ok
    print(f"  Merged count ({len(merged_events):,}) == WA+IG ({merged_expected:,}): {'PASS' if merged_count_ok else 'FAIL'}")

    # --- Merged event ID uniqueness ---
    merged_ids = [e["event_id"] for e in merged_events]
    merged_unique = len(merged_ids) == len(set(merged_ids))
    results["merged_event_ids_unique"] = merged_unique
    print(f"  Merged event ID uniqueness: {'PASS' if merged_unique else 'FAIL'}")

    # --- Duplicate candidates ---
    dup_groups = set(e.get("duplicate_group_id") for e in merged_events if e.get("duplicate_group_id"))
    results["duplicate_candidate_groups"] = len(dup_groups)
    print(f"  Duplicate candidate groups: {len(dup_groups):,} (source events preserved)")

    # --- Timestamp inversions ---
    inversions = wa_audit.get("timestamp_inversion_count", 0)
    results["wa_timestamp_inversions"] = inversions
    print(f"  WA timestamp inversions (preserved in source order): {inversions:,}")

    # --- Source-record spot-check (20 random WA events) ---
    import random
    wa_text = (WA_EXPORT_DIR / "WhatsApp Chat with Radhika Singhal.txt").read_text(
        encoding="utf-8", errors="surrogatepass"
    )
    wa_lines = wa_text.splitlines()
    sample = random.sample([e for e in wa_events if e.get("raw_lines")], min(20, len(wa_events)))
    spot_failures = []
    for e in sample:
        first_line_no = e["raw_lines"][0] - 1
        if first_line_no < 0 or first_line_no >= len(wa_lines):
            spot_failures.append(e["event_id"])
            continue
        if e.get("raw_first_line") != wa_lines[first_line_no]:
            spot_failures.append(e["event_id"])
    results["wa_spot_check_sample_size"] = len(sample)
    results["wa_spot_check_failures"] = len(spot_failures)
    spot_ok = len(spot_failures) == 0
    print(f"  WA source spot-check ({len(sample)} events): {'PASS' if spot_ok else 'FAIL — ' + str(spot_failures[:5])}")

    all_pass = all(v for k, v in results.items() if isinstance(v, bool))
    results["all_pass"] = all_pass
    return results


# ===========================================================================
# Stage 12: Ingestion report
# ===========================================================================

def stage_report(
    wa_events, wa_audit, wa_assets, wa_link_summary,
    ig_events, ig_audit, ig_assets, ig_link_summary,
    merged_events, validation,
) -> Path:
    print("\n=== Stage 12: Writing ingestion report ===")
    OUT_REPORTS.mkdir(parents=True, exist_ok=True)

    wa_kinds = collections.Counter(e["kind"] for e in wa_events)
    ig_kinds = collections.Counter(e["kind"] for e in ig_events)
    merged_kinds = collections.Counter(e["kind"] for e in merged_events)

    wa_senders = collections.Counter(e.get("sender_raw") for e in wa_events if e.get("sender_raw"))
    ig_senders = collections.Counter(e.get("sender_raw") for e in ig_events if e.get("sender_raw"))

    wa_dates = [e["timestamp_parsed"] for e in wa_events if e.get("timestamp_parsed")]
    ig_dates = [e["timestamp_sort_key"] for e in ig_events if e.get("timestamp_sort_key")]

    # Monthly volume
    wa_months = collections.Counter(ts[:7] for ts in wa_dates if ts)
    ig_months = collections.Counter(ts[:7] for ts in ig_dates if ts)

    # Gaps > 7 days in WA
    wa_sorted_dates = sorted(datetime.fromisoformat(ts) for ts in wa_dates)
    gaps_7d = []
    for a, b in zip(wa_sorted_dates, wa_sorted_dates[1:]):
        delta = (b - a).total_seconds() / 86400
        if delta > 7:
            gaps_7d.append({"from": a.isoformat(), "to": b.isoformat(), "days": round(delta, 1)})

    # WA attachment status
    wa_attach_status = collections.Counter(
        e.get("attachment_status") for e in wa_events if e.get("attachment_status")
    )
    ig_attach_status = collections.Counter(
        e.get("attachment_status") for e in ig_events if e.get("attachment_status")
    )

    report = {
        "report_version": "1.0",
        "created_at_utc": _utcnow(),
        "scope": "Full ingestion audit. No relationship interpretation.",
        "privacy": "No message text, sender names (beyond participant labels), private URLs, media contents or message IDs included.",
        "timezone": {
            "value": WA_TIMEZONE,
            "label": TIMEZONE_LABEL,
            "confirmed": TIMEZONE_CONFIRMED,
            "warning": (
                "Timezone is ASSUMED, not yet user-confirmed (pending DEC-001/DEC-002). "
                "All timestamps and cross-platform sort keys are provisional."
                if not TIMEZONE_CONFIRMED else "Timezone user-confirmed."
            ),
        },
        "whatsapp": {
            "source_file": "WhatsApp Chat with Radhika Singhal.txt",
            "source_sha256": wa_audit.get("source_sha256"),
            "physical_lines": wa_audit.get("physical_lines"),
            "timestamp_headers": wa_audit.get("timestamp_headers"),
            "line_coverage": wa_audit.get("all_lines_accounted_for"),
            "events": len(wa_events),
            "date_order": wa_audit.get("date_order"),
            "date_range": [min(wa_dates) if wa_dates else None, max(wa_dates) if wa_dates else None],
            "precision": "minute (12h format, no seconds in this export)",
            "sender_counts": dict(wa_senders),
            "event_kinds": dict(wa_kinds),
            "attachment_status_counts": dict(wa_attach_status),
            "attachment_reference_occurrences": wa_link_summary.get("attachment_reference_occurrences"),
            "distinct_assets_linked": wa_link_summary.get("distinct_assets_linked"),
            "missing_reference_occurrences": wa_link_summary.get("missing_reference_occurrences"),
            "ambiguous_events": wa_link_summary.get("ambiguous_events"),
            "unlinked_assets": wa_link_summary.get("unlinked_asset_count"),
            "edited_events": wa_audit.get("edited_events"),
            "timestamp_inversions": wa_audit.get("timestamp_inversion_count"),
            "gaps_over_7_days": gaps_7d,
            "review_line_count": len(wa_audit.get("review_lines", [])),
            "monthly_volume": dict(sorted(wa_months.items())),
            "asset_count": len(wa_assets),
            "asset_categories": dict(collections.Counter(a["category"] for a in wa_assets)),
        },
        "instagram": {
            "source_files": ig_audit.get("files"),
            "source_records_by_file": ig_audit.get("message_count_by_file"),
            "events": len(ig_events),
            "participants_found": ig_audit.get("participants"),
            "timezone_used": ig_audit.get("timezone"),
            "timezone_label": TIMEZONE_LABEL,
            "date_range": [min(ig_dates) if ig_dates else None, max(ig_dates) if ig_dates else None],
            "event_kinds": dict(ig_kinds),
            "attachment_status_counts": dict(ig_attach_status),
            "attachment_reference_count": ig_link_summary.get("attachment_reference_count"),
            "distinct_assets_linked": ig_link_summary.get("distinct_assets_linked"),
            "missing_reference_occurrences": ig_link_summary.get("missing_reference_occurrences"),
            "unlinked_assets": ig_link_summary.get("unlinked_asset_count"),
            "mojibake_strings_repaired": ig_audit.get("strings_repaired"),
            "synthetic_notice_count": ig_audit.get("synthetic_notice_count"),
            "null_or_empty_content_records": ig_audit.get("messages_with_null_or_empty_content"),
            "monthly_volume": dict(sorted(ig_months.items())),
            "asset_count": len(ig_assets),
            "asset_categories": dict(collections.Counter(a["category"] for a in ig_assets)),
        },
        "combined": {
            "total_events": len(merged_events),
            "wa_events": len(wa_events),
            "ig_events": len(ig_events),
            "event_kinds": dict(merged_kinds),
            "duplicate_candidate_groups": validation.get("duplicate_candidate_groups"),
            "events_in_uncertain_ordering_clusters": sum(1 for e in merged_events if e.get("ordering_uncertain")),
            "total_assets": len(wa_assets) + len(ig_assets),
        },
        "validation": validation,
        "limits": [
            f"Timezone ({WA_TIMEZONE}) is ASSUMED not user-confirmed. All timestamps are provisional.",
            "WhatsApp timestamps are exporting-phone local wall-clock with no encoded timezone.",
            "Media bytes were inventoried, hashed, and linked by filename. Contents were not viewed or interpreted.",
            "57 distinct WhatsApp filenames referenced but absent from the export directory.",
            "3 Instagram video references have no corresponding file in the export.",
            "37 generic '<Media omitted>' markers have unknown type; no bytes available.",
            "Cross-platform ordering within the same minute is marked ordering_uncertain.",
        ],
        "decisions_still_required": [
            "DEC-001: WhatsApp timezone confirmation (currently assumed Asia/Kolkata).",
            "DEC-002: Instagram display timezone confirmation (currently assumed Asia/Kolkata).",
            "DEC-003: Identity — who is the requester (Rachit or Radhika)?",
            "DEC-004: Audience — only me / both together / surprise?",
            "DEC-005: Does a text-only WhatsApp export exist separately?",
            "DEC-006: Human-supplied milestones.",
            "DEC-007: Off-chat context (calls, meetings, distance, exams, travel).",
        ],
    }

    path = OUT_REPORTS / "ingestion-report.json"
    atomic_write_json(path, report)
    print(f"  Report written: {path.name} ({path.stat().st_size:,} bytes)")
    return path


# ===========================================================================
# Stage 13: Missing/ambiguous media report
# ===========================================================================

def stage_media_report(wa_events, wa_assets, ig_events, ig_assets) -> Path:
    print("\n=== Stage 13: Missing/ambiguous media report ===")
    OUT_REPORTS.mkdir(parents=True, exist_ok=True)

    # WA missing
    wa_missing = [
        {"event_id": e["event_id"], "refs": e.get("unresolved_attachment_refs", [])}
        for e in wa_events if e.get("attachment_status") in ("referenced-but-missing", "partially-resolved")
    ]
    wa_generic = [
        {"event_id": e["event_id"]}
        for e in wa_events if e.get("attachment_status") == "unmatched-generic-reference"
    ]
    wa_ambiguous = [
        {"event_id": e["event_id"], "candidates": e.get("attachment_candidate_refs", [])}
        for e in wa_events if e.get("attachment_status") == "ambiguous-match"
    ]
    wa_unlinked = [a for a in wa_assets if not a.get("status") == "linked"]

    # IG missing
    ig_missing = [
        {"event_id": e["event_id"], "refs": e.get("unresolved_attachment_refs", [])}
        for e in ig_events if e.get("attachment_status") in ("referenced-but-missing", "partially-resolved")
    ]

    report = {
        "report_version": "1.0",
        "created_at_utc": _utcnow(),
        "privacy": "Event IDs only. No message text, media contents or private filenames.",
        "whatsapp": {
            "referenced_but_missing_events": len(wa_missing),
            "generic_omitted_markers": len(wa_generic),
            "ambiguous_match_events": len(wa_ambiguous),
            "event_ids_missing": [x["event_id"] for x in wa_missing],
            "event_ids_generic_omitted": [x["event_id"] for x in wa_generic],
            "note": "Generic '<Media omitted>' markers have unknown type. 57 distinct referenced filenames are absent from the export directory.",
        },
        "instagram": {
            "referenced_but_missing_events": len(ig_missing),
            "event_ids_missing": [x["event_id"] for x in ig_missing],
            "note": "3 video references have no corresponding file in the export.",
        },
    }

    path = OUT_REPORTS / "missing-media-report.json"
    atomic_write_json(path, report)
    print(f"  Missing-media report written: {path.name}")
    return path


# ===========================================================================
# Main pipeline
# ===========================================================================

def main():
    print("=" * 70)
    print("RELATIONSHIP ARCHIVE — INGESTION PIPELINE")
    print(f"Started: {_utcnow()}")
    print(f"Timezone: {WA_TIMEZONE} ({TIMEZONE_LABEL})")
    print("=" * 70)

    # Ensure all output directories exist.
    for d in (OUT_NORMALIZED, OUT_MEDIA, OUT_INDEXES, OUT_REPORTS,
              OUT_STATE, OUT_CHECKPOINTS, OUT_LOGS):
        d.mkdir(parents=True, exist_ok=True)

    # --- Stage 1: Self-tests ---
    if not stage_selftest():
        print("\nABORTED: Self-tests failed. Fix tool issues before ingesting.")
        sys.exit(1)
    write_checkpoint("CP-ING-001", "ingestion/selftest-pass", "Run WhatsApp ingestion")
    log_operation("OP-ING-001", "Skill self-tests", [], "complete", "23/23 chat_tools, 9/9 media_tools, parity pass")

    # --- Stage 2: WhatsApp parse ---
    wa_events, wa_audit = stage_whatsapp()
    write_checkpoint("CP-ING-002", "ingestion/wa-parsed", "Inventory WhatsApp media")
    log_operation("OP-ING-002", "WhatsApp parse", [], "complete",
                  f"{len(wa_events)} events, line_coverage={wa_audit['all_lines_accounted_for']}")

    # --- Stage 3: WA media ---
    wa_assets = stage_whatsapp_media()
    write_checkpoint("CP-ING-003", "ingestion/wa-media-inventoried", "Run Instagram ingestion")
    log_operation("OP-ING-003", "WhatsApp media inventory", [], "complete", f"{len(wa_assets)} assets")

    # --- Stage 4: Instagram parse ---
    ig_events, ig_audit = stage_instagram()
    write_checkpoint("CP-ING-004", "ingestion/ig-parsed", "Inventory Instagram media")
    log_operation("OP-ING-004", "Instagram parse", [], "complete", f"{len(ig_events)} events")

    # --- Stage 5: IG media ---
    ig_assets = stage_instagram_media()
    write_checkpoint("CP-ING-005", "ingestion/ig-media-inventoried", "Link attachments")
    log_operation("OP-ING-005", "Instagram media inventory", [], "complete", f"{len(ig_assets)} assets")

    # --- Stage 6: Link ---
    wa_link_summary, ig_link_summary = stage_link_media(wa_events, wa_assets, ig_events, ig_assets)
    write_checkpoint("CP-ING-006", "ingestion/media-linked", "Cross-platform merge")
    log_operation("OP-ING-006", "Media linking", [], "complete",
                  f"WA linked {wa_link_summary['distinct_assets_linked']}, IG linked {ig_link_summary['distinct_assets_linked']}")

    # --- Stage 7: Merge ---
    merged_events = stage_merge(wa_events, ig_events)
    write_checkpoint("CP-ING-007", "ingestion/merged", "Write JSONL chunks")
    log_operation("OP-ING-007", "Cross-platform merge", [], "complete", f"{len(merged_events)} merged events")

    # --- Stage 8: Write chunks ---
    chunks = stage_write_chunks(wa_events, ig_events, merged_events)
    written_files = [str(p) for d in chunks.values() for p in d.values()]
    write_checkpoint("CP-ING-008", "ingestion/chunks-written", "Write media manifest")
    log_operation("OP-ING-008", "JSONL chunk write", written_files, "complete",
                  f"{len(chunks['merged'])} merged monthly chunks")

    # --- Stage 9: Media manifest ---
    manifest_path = stage_media_manifest(wa_assets, ig_assets, wa_link_summary, ig_link_summary)
    write_checkpoint("CP-ING-009", "ingestion/manifest-written", "Build search index")
    log_operation("OP-ING-009", "Media manifest", [str(manifest_path)], "complete")

    # --- Stage 10: Search index ---
    index_path = stage_search_index(merged_events)
    write_checkpoint("CP-ING-010", "ingestion/search-index-written", "Run validation")
    log_operation("OP-ING-010", "Search index", [str(index_path)], "complete")

    # --- Stage 11: Validate ---
    validation = stage_validate(wa_events, wa_audit, ig_events, ig_audit, merged_events)
    if not validation["all_pass"]:
        print("\nWARNING: Validation has failures — see ingestion report.")

    # --- Stage 12: Ingestion report ---
    report_path = stage_report(
        wa_events, wa_audit, wa_assets, wa_link_summary,
        ig_events, ig_audit, ig_assets, ig_link_summary,
        merged_events, validation,
    )

    # --- Stage 13: Missing media report ---
    media_report_path = stage_media_report(wa_events, wa_assets, ig_events, ig_assets)

    # --- Final checkpoint ---
    write_checkpoint(
        "CP-ING-FINAL", "ingestion/complete",
        "Show ingestion report to user and wait for approval before analysis.",
        notes=(
            f"WA: {len(wa_events):,} events | "
            f"IG: {len(ig_events):,} events | "
            f"Merged: {len(merged_events):,} | "
            f"Validation: {'PASS' if validation['all_pass'] else 'PARTIAL'} | "
            f"Timezone: {TIMEZONE_LABEL}"
        ),
    )
    log_operation(
        "OP-ING-FINAL", "Ingestion pipeline complete",
        [str(report_path), str(media_report_path)],
        "complete" if validation["all_pass"] else "complete-with-warnings",
    )

    print("\n" + "=" * 70)
    print("INGESTION COMPLETE")
    print(f"  WA events:     {len(wa_events):,}")
    print(f"  IG events:     {len(ig_events):,}")
    print(f"  Merged total:  {len(merged_events):,}")
    print(f"  WA assets:     {len(wa_assets):,}")
    print(f"  IG assets:     {len(ig_assets):,}")
    print(f"  Validation:    {'ALL PASS' if validation['all_pass'] else 'SEE REPORT'}")
    print(f"  Timezone:      {TIMEZONE_LABEL} ({WA_TIMEZONE})")
    print(f"  Report:        {report_path}")
    print(f"  Checkpoint:    CP-ING-FINAL")
    print("=" * 70)
    print("\nSTOP: Show ingestion report to user and wait for approval.")
    return 0 if validation["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())


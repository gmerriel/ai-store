"""
skill4_ad_video_writer.py — Phase 4 of the Creative Intelligence Pipeline.

Read transcriptions (Skill 1) and concepts (Skill 2). Generate complete video
scripts with hook staging. Save to Supabase and markdown.

Usage:
    python3 skill4_ad_video_writer.py --account profitable_tradie --funnel labour_calc --week 2026-03-10
"""

import argparse
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from creative_config import (
    ACCOUNTS,
    ensure_dir,
    get_openai_client,
    get_supabase_client,
    get_week_str,
)

# ─── CONSTANTS ────────────────────────────────────────────────────────────────

BLOCKED = [
    "drinking",
    "sipping",
    "eating",
    "chewing",
    "drilling",
    "hammering",
    "sawing",
    "driving",
    "on the phone",
    "on a call",
]

# ─── PARSER HELPERS ──────────────────────────────────────────────────────────


def _extract_block(text: str, start_tag: str, end_tag: str) -> str:
    """Extract text between start_tag and end_tag."""
    pattern = re.compile(
        re.escape(start_tag) + r"(.*?)" + re.escape(end_tag),
        re.DOTALL,
    )
    m = pattern.search(text)
    return m.group(1).strip() if m else ""


def _extract_field(block: str, field: str) -> str:
    """Extract a single-line field value."""
    pattern = re.compile(r"^" + re.escape(field) + r":\s*(.+)$", re.MULTILINE)
    m = pattern.search(block)
    return m.group(1).strip() if m else ""


def _extract_multiline_field(block: str, field: str) -> str:
    """Extract everything after a field marker until next field or end."""
    pattern = re.compile(r"^" + re.escape(field) + r":\s*\n?(.*)", re.DOTALL | re.MULTILINE)
    m = pattern.search(block)
    if not m:
        return ""
    content = m.group(1)
    # Stop at next ALL_CAPS_FIELD: line
    stop = re.search(r"\n[A-Z_]+:\s", content)
    if stop:
        content = content[: stop.start()]
    return content.strip()


def validate_action(action: str) -> Tuple[bool, List[str]]:
    """Check action against blocked words list. Returns (is_valid, flagged_words)."""
    action_lower = action.lower()
    flagged = [word for word in BLOCKED if word in action_lower]
    return len(flagged) == 0, flagged


def parse_video_scripts(response_text: str) -> List[Dict[str, Any]]:
    """Parse SCRIPT_START/SCRIPT_END blocks from GPT-4o response."""
    scripts = []
    blocks = re.split(r"SCRIPT_START", response_text)
    for block in blocks[1:]:
        end_idx = block.find("SCRIPT_END")
        if end_idx != -1:
            block = block[:end_idx]

        script_id = _extract_field(block, "SCRIPT_ID")
        hook_text = _extract_field(block, "HOOK_TEXT")
        location = _extract_field(block, "LOCATION")
        prop = _extract_field(block, "PROP")
        action = _extract_field(block, "ACTION")
        directors_note = _extract_field(block, "DIRECTORS_NOTE")
        full_script = _extract_multiline_field(block, "FULL_SCRIPT")
        estimated_seconds_str = _extract_field(block, "ESTIMATED_SECONDS")
        energy = _extract_field(block, "ENERGY")

        try:
            estimated_seconds = int(estimated_seconds_str)
        except ValueError:
            estimated_seconds = 0

        if not script_id:
            continue

        # Validate action
        is_valid, flagged_words = validate_action(action)
        action_warning = ""
        if not is_valid:
            action_warning = (
                f"⚠️ WARNING: Blocked action detected — contains: {', '.join(flagged_words)}"
            )
            print(f"  [WARN] Script {script_id}: {action_warning}")

        scripts.append({
            "script_id": script_id,
            "hook_text": hook_text,
            "location": location,
            "prop": prop,
            "action": action,
            "action_valid": is_valid,
            "action_warning": action_warning,
            "directors_note": directors_note,
            "full_script": full_script,
            "estimated_seconds": estimated_seconds,
            "energy": energy,
        })

    return scripts


# ─── PROMPT BUILDER ──────────────────────────────────────────────────────────


def _build_ad_variants_section(
    concepts_data: List[Dict[str, Any]],
    funnel_cfg: Dict[str, Any],
) -> Tuple[str, List[Dict]]:
    """Build the AD VARIANTS section and return (text, flat_list)."""
    lines = []
    flat_variants = []
    cta = funnel_cfg.get("cta", "")

    for c in concepts_data:
        concept_id = c.get("concept_id", "")
        hooks_a = (
            json.loads(c.get("hooks_a", "[]"))
            if isinstance(c.get("hooks_a"), str)
            else (c.get("hooks_a") or [])
        )
        hooks_b = (
            json.loads(c.get("hooks_b", "[]"))
            if isinstance(c.get("hooks_b"), str)
            else (c.get("hooks_b") or [])
        )

        for body_ref, hooks, body_copy in [
            ("A", hooks_a, c.get("body_a", "")),
            ("B", hooks_b, c.get("body_b", "")),
        ]:
            for h in hooks:
                variant_id = f"{concept_id}_{body_ref}_H{h['index']}"
                lines += [
                    f"VARIANT: {variant_id}",
                    f"HOOK TEXT (spoken word-for-word): {h['text']}",
                    f"BODY COPY (format for speech): {body_copy}",
                    f"CTA: {cta}",
                    f"HOOK TYPE: {h['type']}",
                    "",
                ]
                flat_variants.append({
                    "variant_id": variant_id,
                    "concept_id": concept_id,
                    "body_ref": body_ref,
                    "hook_index": h["index"],
                    "hook_type": h["type"],
                    "hook_text": h["text"],
                    "body_copy": body_copy,
                    "cta": cta,
                })

    return "\n".join(lines), flat_variants


def build_prompt(
    audience: str,
    offer_name: str,
    transcripts: List[Dict[str, Any]],
    concepts_data: List[Dict[str, Any]],
    funnel_cfg: Dict[str, Any],
) -> Tuple[str, List[Dict]]:
    """Build the GPT-4o prompt for video script generation."""

    transcript_section = ""
    for t in transcripts:
        transcript_section += (
            f"VIDEO #{t.get('rank')} | CPL ${t.get('cpl', 0):.2f}\n"
            f"Hook: {t.get('hook_text', '')}\n"
            f"Full: {t.get('full_transcript', '')}\n\n"
        )
    if not transcript_section:
        transcript_section = "(No video transcripts available — write from concepts only.)\n"

    variants_section, flat_variants = _build_ad_variants_section(concepts_data, funnel_cfg)

    prompt = f"""You are a UGC video ad director and direct response copywriter.
Audience: {audience}
Offer: {offer_name}

TOP VIDEO BENCHMARKS (what's working — transcribed):
{transcript_section}
For each ad variant below, write a complete video script.
The hook gets LOCATION + PROP + ACTION staging directions.
The body and CTA come from the copy — format for speech (natural pauses, short lines).

STAGING RULES:
- Location: authentic to trades business owners (ute, job site, workshop, kitchen table at night) — never café, office, gym
- Prop: everyday niche-relevant item (clipboard, hard hat held not worn, work gloves, keys, takeaway cup not being drunk from, printed quote/invoice)
- Action: subtle, interruptible — person pauses what they're doing to speak. CANNOT block speech.
- BLOCKED ACTIONS: drinking, eating, drilling, operating tools, driving, talking on phone

AD VARIANTS:
{variants_section}
For each variant output:
SCRIPT_START
SCRIPT_ID: [variant_id]_VID
HOOK_TEXT: [exact hook from above — no changes]
LOCATION: [one sentence]
PROP: [one sentence]
ACTION: [one sentence — must not block speech]
DIRECTORS_NOTE: [one sentence — visual mood in first 2 seconds]
FULL_SCRIPT:
[HOOK]
"[hook text]"

[BODY]
"[body copy broken into spoken units, new line = pause]"

[CTA]
"[cta]"
ESTIMATED_SECONDS: [number]
ENERGY: [calm/medium/urgent]
SCRIPT_END"""

    return prompt, flat_variants


# ─── MARKDOWN OUTPUT ─────────────────────────────────────────────────────────


def write_markdown(
    report_dir: str,
    funnel: str,
    week_start: str,
    account_key: str,
    transcripts: List[Dict[str, Any]],
    scripts: List[Dict[str, Any]],
) -> str:
    """Write the video brief markdown and return its path."""
    ensure_dir(report_dir)
    output_path = os.path.join(report_dir, f"video_brief_{funnel}_{week_start}.md")
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        f"# Video Brief — {account_key} / {funnel}",
        f"",
        f"**Generated:** {timestamp}  ",
        f"**Week:** {week_start}  ",
        f"**Funnel:** {funnel}  ",
        f"",
        f"---",
        f"",
        f"## Video Benchmarks",
        f"",
    ]

    if transcripts:
        for t in transcripts:
            lines += [
                f"**VIDEO #{t.get('rank')} | CPL ${t.get('cpl', 0):.2f} | {t.get('conversions', 0)} leads**",
                f"",
                f"Hook: {t.get('hook_text', '')}",
                f"",
                f"<details><summary>Full Transcript</summary>",
                f"",
                f"{t.get('full_transcript', '')}",
                f"",
                f"</details>",
                f"",
            ]
    else:
        lines += ["*(No video transcripts available)*", ""]

    lines += ["---", "", f"## Video Scripts ({len(scripts)} total)", ""]

    for s in scripts:
        hook_flag = " ⚠️" if not s["action_valid"] else ""
        lines += [
            f"### {s['script_id']}{hook_flag}",
            f"",
            f"**Energy:** {s['energy']}  ",
            f"**Estimated duration:** ~{s['estimated_seconds']}s",
            f"",
            f"#### Staging",
            f"",
            f"| | |",
            f"|---|---|",
            f"| **Location** | {s['location']} |",
            f"| **Prop** | {s['prop']} |",
            f"| **Action** | {s['action']} |",
            f"| **Director's note** | {s['directors_note']} |",
            f"",
        ]
        if s["action_warning"]:
            lines += [f"> {s['action_warning']}", f""]

        lines += [
            f"#### Full Script (Teleprompter)",
            f"",
            f"```",
            s["full_script"],
            f"```",
            f"",
            f"---",
            f"",
        ]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  [MD] Written: {output_path}")
    return output_path


# ─── MAIN ────────────────────────────────────────────────────────────────────


def run(account_key: str, funnel: str, week_start: str) -> None:
    """Run Skill 4 for the given account, funnel, and week."""
    if account_key not in ACCOUNTS:
        raise ValueError(f"Unknown account key: {account_key}")

    account = ACCOUNTS[account_key]
    client_slug = account["client_slug"]
    week_str = get_week_str(week_start)
    report_dir = account["report_dir"]
    audience = account["audience"]
    funnel_cfg = account["funnels"].get(funnel)
    if not funnel_cfg:
        raise ValueError(f"Unknown funnel '{funnel}' for account '{account_key}'")
    offer_name = funnel_cfg["offer_name"]

    supabase = get_supabase_client()
    openai_client = get_openai_client()

    print(f"\n{'='*60}")
    print(f"  Skill 4 — Ad Video Writer")
    print(f"  Account : {account_key}")
    print(f"  Funnel  : {funnel}")
    print(f"  Week    : {week_start} ({week_str})")
    print(f"{'='*60}")

    # ── Read Supabase data ──
    print("\n[4] Reading video transcriptions from Supabase…")
    try:
        trans_resp = (
            supabase.table("ad_video_transcriptions")
            .select("*")
            .eq("account_id", account["account_id"])
            .eq("funnel_name", funnel)
            .eq("week_start", week_start)
            .order("rank")
            .execute()
        )
        transcripts = trans_resp.data or []
    except Exception as exc:
        print(f"  [WARN] Failed to read ad_video_transcriptions: {exc}")
        transcripts = []

    if not transcripts:
        print("  [NOTE] No video transcriptions found — will generate scripts from concepts only.")

    print(f"  Reading concepts from Supabase…")
    try:
        concepts_resp = (
            supabase.table("ad_concepts")
            .select("*")
            .eq("account_id", account["account_id"])
            .eq("funnel_name", funnel)
            .eq("week_start", week_start)
            .execute()
        )
        concepts_data = concepts_resp.data or []
    except Exception as exc:
        raise RuntimeError(f"Failed to read ad_concepts: {exc}") from exc

    if not concepts_data:
        raise RuntimeError("No concepts found. Run Skill 2 first.")

    print(f"  Transcripts: {len(transcripts)}, Concepts: {len(concepts_data)}")

    # ── Build prompt ──
    print("\n[4] Building GPT-4o prompt…")
    prompt, flat_variants = build_prompt(audience, offer_name, transcripts, concepts_data, funnel_cfg)

    # ── Call GPT-4o ──
    print("[4] Calling GPT-4o for video script generation…")
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=8192,
            temperature=0.7,
        )
        response_text = response.choices[0].message.content or ""
    except Exception as exc:
        raise RuntimeError(f"GPT-4o call failed: {exc}") from exc

    # ── Parse response ──
    scripts = parse_video_scripts(response_text)
    print(f"  Parsed {len(scripts)} script(s).")

    blocked_count = sum(1 for s in scripts if not s["action_valid"])
    if blocked_count:
        print(f"  [WARN] {blocked_count} script(s) have blocked action words — flagged in output.")

    # ── Save to Supabase ──
    for s in scripts:
        script_id = s["script_id"]
        row = {
            "script_id": script_id,
            "account_id": account["account_id"],
            "funnel_name": funnel,
            "week_start": week_start,
            "hook_text": s["hook_text"],
            "location": s["location"],
            "prop": s["prop"],
            "action": s["action"],
            "action_valid": s["action_valid"],
            "action_warning": s["action_warning"],
            "directors_note": s["directors_note"],
            "full_script": s["full_script"],
            "estimated_seconds": s["estimated_seconds"],
            "energy": s["energy"],
        }
        try:
            supabase.table("ad_video_scripts").upsert(row, on_conflict="script_id").execute()
            print(f"  [DB] Upserted ad_video_scripts: {script_id}")
        except Exception as exc:
            print(f"  [ERROR] Supabase upsert failed for {script_id}: {exc}")

    # ── Write markdown ──
    write_markdown(report_dir, funnel, week_start, account_key, transcripts, scripts)

    print(f"\n{'='*60}")
    print(f"  Skill 4 COMPLETE — {len(scripts)} script(s) generated.")
    if blocked_count:
        print(f"  ⚠️  {blocked_count} blocked action warning(s) — review before production.")
    print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Skill 4 — Ad Video Writer")
    parser.add_argument("--account", required=True, help="Account key (e.g. profitable_tradie)")
    parser.add_argument("--funnel", required=True, help="Funnel key (e.g. labour_calc)")
    parser.add_argument("--week", required=True, help="Week start date YYYY-MM-DD")
    args = parser.parse_args()
    run(args.account, args.funnel, args.week)

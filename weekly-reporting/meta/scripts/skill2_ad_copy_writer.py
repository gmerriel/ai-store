"""
skill2_ad_copy_writer.py — Phase 2 of the Creative Intelligence Pipeline.

Read winners from Supabase. Generate 2 concepts × 2 bodies × 5 hooks using GPT-4o.
Save to Supabase and markdown.

Usage:
    python3 skill2_ad_copy_writer.py --account profitable_tradie --funnel labour_calc --week 2026-03-10
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

# ─── PARSER HELPERS ──────────────────────────────────────────────────────────


def _extract_block(text: str, start_tag: str, end_tag: str) -> str:
    """Extract text between start_tag and end_tag (exclusive)."""
    pattern = re.compile(
        re.escape(start_tag) + r"(.*?)" + re.escape(end_tag),
        re.DOTALL,
    )
    m = pattern.search(text)
    return m.group(1).strip() if m else ""


def _extract_field(text: str, field: str) -> str:
    """Extract a single-line field like 'CONCEPT_ID: C1'."""
    pattern = re.compile(r"^" + re.escape(field) + r":\s*(.+)$", re.MULTILINE)
    m = pattern.search(text)
    return m.group(1).strip() if m else ""


def _count_words(text: str) -> int:
    return len(text.split())


def _parse_hooks(concept_block: str, body_ref: str) -> List[Dict[str, Any]]:
    """Parse HOOK_{body_ref}1..5 blocks from a concept block."""
    hooks = []
    for i in range(1, 6):
        tag_start = f"HOOK_{body_ref}{i}_START"
        tag_end = f"HOOK_{body_ref}{i}_END"
        hook_block = _extract_block(concept_block, tag_start, tag_end)
        if not hook_block:
            continue
        hook_type = _extract_field(hook_block, "TYPE")
        hook_text = _extract_field(hook_block, "TEXT")
        if not hook_text:
            # Fallback: everything after "TEXT:" line
            m = re.search(r"TEXT:\s*(.*)", hook_block, re.DOTALL)
            hook_text = m.group(1).strip() if m else hook_block
        hooks.append({
            "index": i,
            "type": hook_type.lower(),
            "text": hook_text,
            "word_count": _count_words(hook_text),
        })
    return hooks


def parse_gpt_response(response_text: str) -> List[Dict[str, Any]]:
    """
    Parse GPT-4o structured response into a list of concept dicts.

    Each concept dict has:
        concept_num, concept_name, inspired_by, headline,
        body_a, hooks_a, body_b, hooks_b
    """
    concepts = []
    concept_blocks = re.split(r"CONCEPT_START", response_text)
    for block in concept_blocks[1:]:  # skip text before first CONCEPT_START
        end_idx = block.find("CONCEPT_END")
        if end_idx != -1:
            block = block[:end_idx]

        concept_id_str = _extract_field(block, "CONCEPT_ID")
        concept_num = concept_id_str.replace("C", "").strip()
        concept_name = _extract_field(block, "CONCEPT_NAME")
        inspired_by = _extract_field(block, "INSPIRED_BY")
        headline = _extract_field(block, "HEADLINE")

        body_a = _extract_block(block, "BODY_A_START", "BODY_A_END")
        body_b = _extract_block(block, "BODY_B_START", "BODY_B_END")

        hooks_a = _parse_hooks(block, "A")
        hooks_b = _parse_hooks(block, "B")

        if not concept_num:
            continue

        concepts.append({
            "concept_num": concept_num,
            "concept_name": concept_name,
            "inspired_by": inspired_by,
            "headline": headline,
            "body_a": body_a,
            "hooks_a": hooks_a,
            "body_b": body_b,
            "hooks_b": hooks_b,
        })

    return concepts


# ─── PROMPT BUILDER ──────────────────────────────────────────────────────────


def build_prompt(
    audience: str,
    offer_name: str,
    transcripts: List[Dict[str, Any]],
    image_winners: List[Dict[str, Any]],
) -> str:
    """Build the GPT-4o prompt for ad copy generation."""

    transcript_section = ""
    for t in transcripts:
        transcript_section += (
            f"VIDEO #{t.get('rank')} | CPL ${t.get('cpl', 0):.2f} | "
            f"{t.get('conversions', 0)} leads\n"
            f"Hook: {t.get('hook_text', '')}\n"
            f"Full transcript:\n{t.get('full_transcript', '')}\n\n"
        )
    if not transcript_section:
        transcript_section = "(No video transcripts available for this funnel/week.)\n"

    image_section = ""
    for img in image_winners:
        image_section += (
            f"IMAGE #{img.get('rank')} | CPL ${img.get('cpl', 0):.2f} | "
            f"{img.get('conversions', 0)} leads\n"
            f"Headline: {img.get('headline', '')}\n"
            f"Caption: {img.get('body_copy', '')}\n\n"
        )
    if not image_section:
        image_section = "(No image captions available for this funnel/week.)\n"

    prompt = f"""You are a direct response copywriter for Facebook/Instagram ads.
Audience: {audience}
Offer: {offer_name}

PRIORITY SOURCE — VIDEO TRANSCRIPTS (actual spoken words driving results):
{transcript_section}
SUPPORTING SOURCE — IMAGE AD CAPTIONS:
{image_section}
Write 2 concepts. Each concept has 2 body copies (150-200 words each) and 5 hooks per body (35-55 words each).

HOOK TYPES:
- H1, H2 = CONTINUER: Almost identical to the proven winners above. Same opening line, same emotional entry point. Do NOT reinvent. Retain.
- H3, H4, H5 = EXPLORER: Same emotional foundation, new angle or entry point.

MANDATORY:
- First 10 words of every hook signal the niche via actions/pains — NOT by naming "tradie/plumber/etc"
- Use real numbers from transcripts (especially for Continuers)
- Count words (150-200 body, 35-55 hooks)
- Note which source inspired each concept

OUTPUT FORMAT (strict — parse this):
CONCEPT_START
CONCEPT_ID: C1
CONCEPT_NAME: [name]
INSPIRED_BY: [source ad name and CPL]
HEADLINE: [headline]
BODY_A_START
[150-200 word body]
BODY_A_END
HOOK_A1_START
TYPE: continuer
TEXT: [35-55 word hook]
HOOK_A1_END
HOOK_A2_START
TYPE: continuer
TEXT: [hook]
HOOK_A2_END
HOOK_A3_START
TYPE: explorer
TEXT: [hook]
HOOK_A3_END
HOOK_A4_START
TYPE: explorer
TEXT: [hook]
HOOK_A4_END
HOOK_A5_START
TYPE: explorer
TEXT: [hook]
HOOK_A5_END
BODY_B_START
[150-200 word body]
BODY_B_END
HOOK_B1_START
TYPE: continuer
TEXT: [hook]
HOOK_B1_END
HOOK_B2_START
TYPE: continuer
TEXT: [hook]
HOOK_B2_END
HOOK_B3_START
TYPE: explorer
TEXT: [hook]
HOOK_B3_END
HOOK_B4_START
TYPE: explorer
TEXT: [hook]
HOOK_B4_END
HOOK_B5_START
TYPE: explorer
TEXT: [hook]
HOOK_B5_END
CONCEPT_END
CONCEPT_START
CONCEPT_ID: C2
[same structure]
CONCEPT_END"""

    return prompt


# ─── MARKDOWN OUTPUT ─────────────────────────────────────────────────────────


def write_markdown(
    report_dir: str,
    funnel: str,
    week_start: str,
    account_key: str,
    transcripts: List[Dict[str, Any]],
    image_winners: List[Dict[str, Any]],
    concepts: List[Dict[str, Any]],
) -> str:
    """Write the copy brief markdown file and return its path."""
    ensure_dir(report_dir)
    output_path = os.path.join(report_dir, f"copy_brief_{funnel}_{week_start}.md")
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        f"# Copy Brief — {account_key} / {funnel}",
        f"",
        f"**Generated:** {timestamp}  ",
        f"**Week:** {week_start}  ",
        f"**Funnel:** {funnel}  ",
        f"",
        f"---",
        f"",
        f"## Winner Analysis",
        f"",
    ]

    if transcripts:
        lines.append("### Video Transcripts (Priority Source)")
        lines.append("")
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
        lines.append("*(No video transcripts available)*")
        lines.append("")

    if image_winners:
        lines.append("### Image Ad Captions (Supporting Source)")
        lines.append("")
        for img in image_winners:
            lines += [
                f"**IMAGE #{img.get('rank')} | CPL ${img.get('cpl', 0):.2f} | {img.get('conversions', 0)} leads**",
                f"",
                f"Headline: {img.get('headline', '')}",
                f"",
                f"Caption: {img.get('body_copy', '')}",
                f"",
            ]
    else:
        lines.append("*(No image captions available)*")
        lines.append("")

    lines += ["---", "", "## New Concepts", ""]

    for c in concepts:
        lines += [
            f"### Concept C{c['concept_num']}: {c['concept_name']}",
            f"",
            f"**Inspired by:** {c['inspired_by']}  ",
            f"**Headline:** {c['headline']}",
            f"",
            f"#### Body A ({_count_words(c['body_a'])} words)",
            f"",
            c["body_a"],
            f"",
        ]
        for h in c.get("hooks_a", []):
            label = "CONTINUER" if h["type"] == "continuer" else "EXPLORER"
            lines += [
                f"**Hook A{h['index']} [{label}]** ({h['word_count']} words)",
                f"",
                f"> {h['text']}",
                f"",
            ]

        lines += [
            f"#### Body B ({_count_words(c['body_b'])} words)",
            f"",
            c["body_b"],
            f"",
        ]
        for h in c.get("hooks_b", []):
            label = "CONTINUER" if h["type"] == "continuer" else "EXPLORER"
            lines += [
                f"**Hook B{h['index']} [{label}]** ({h['word_count']} words)",
                f"",
                f"> {h['text']}",
                f"",
            ]
        lines.append("---")
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  [MD] Written: {output_path}")
    return output_path


# ─── MAIN ────────────────────────────────────────────────────────────────────


def run(account_key: str, funnel: str, week_start: str) -> None:
    """Run Skill 2 for the given account, funnel, and week."""
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
    print(f"  Skill 2 — Ad Copy Writer")
    print(f"  Account : {account_key}")
    print(f"  Funnel  : {funnel}")
    print(f"  Week    : {week_start} ({week_str})")
    print(f"{'='*60}")

    # ── Read Supabase data ──
    print("\n[2] Reading winners from Supabase…")

    try:
        copy_resp = (
            supabase.table("ad_copy_winners")
            .select("*")
            .eq("account_id", account["account_id"])
            .eq("funnel_name", funnel)
            .eq("week_start", week_start)
            .order("rank")
            .execute()
        )
        copy_winners = copy_resp.data or []
    except Exception as exc:
        print(f"  [ERROR] Failed to read ad_copy_winners: {exc}")
        copy_winners = []

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
        print(f"  [ERROR] Failed to read ad_video_transcriptions: {exc}")
        transcripts = []

    if not copy_winners and not transcripts:
        raise RuntimeError(
            "No data found in ad_copy_winners or ad_video_transcriptions. Run Skill 1 first."
        )

    image_winners = [w for w in copy_winners if w.get("asset_type") == "image"]

    print(f"  Transcripts: {len(transcripts)}, Image winners: {len(image_winners)}")

    # ── Build prompt and call GPT-4o ──
    print("\n[2] Calling GPT-4o for copy generation…")
    prompt = build_prompt(audience, offer_name, transcripts, image_winners)

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.7,
        )
        response_text = response.choices[0].message.content or ""
    except Exception as exc:
        raise RuntimeError(f"GPT-4o call failed: {exc}") from exc

    # ── Parse response ──
    concepts = parse_gpt_response(response_text)
    print(f"  Parsed {len(concepts)} concept(s) from GPT-4o response.")

    # ── Save to Supabase ──
    source_refs = [
        {"ad_id": t.get("ad_id"), "cpl": t.get("cpl"), "type": "video"} for t in transcripts
    ] + [
        {"ad_id": img.get("ad_id"), "cpl": img.get("cpl"), "type": "image"} for img in image_winners
    ]

    for c in concepts:
        concept_id = f"{client_slug}_{funnel}_C{c['concept_num']}_{week_str}"
        row = {
            "concept_id": concept_id,
            "account_id": account["account_id"],
            "client_slug": client_slug,
            "funnel_name": funnel,
            "week_start": week_start,
            "concept_num": c["concept_num"],
            "concept_name": c["concept_name"],
            "inspired_by": c["inspired_by"],
            "headline": c["headline"],
            "body_a": c["body_a"],
            "body_b": c["body_b"],
            "hooks_a": json.dumps(c["hooks_a"]),
            "hooks_b": json.dumps(c["hooks_b"]),
            "source_refs": json.dumps(source_refs),
        }
        try:
            supabase.table("ad_concepts").upsert(row, on_conflict="concept_id").execute()
            print(f"  [DB] Upserted ad_concepts: {concept_id}")
        except Exception as exc:
            print(f"  [ERROR] Supabase upsert failed for {concept_id}: {exc}")

    # ── Write markdown ──
    write_markdown(
        report_dir, funnel, week_start, account_key,
        transcripts, image_winners, concepts,
    )

    print(f"\n{'='*60}")
    print(f"  Skill 2 COMPLETE — {len(concepts)} concept(s) generated.")
    print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Skill 2 — Ad Copy Writer")
    parser.add_argument("--account", required=True, help="Account key (e.g. profitable_tradie)")
    parser.add_argument("--funnel", required=True, help="Funnel key (e.g. labour_calc)")
    parser.add_argument("--week", required=True, help="Week start date YYYY-MM-DD")
    args = parser.parse_args()
    run(args.account, args.funnel, args.week)

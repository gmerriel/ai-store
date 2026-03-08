"""
skill3_ad_image_writer.py — Phase 3 of the Creative Intelligence Pipeline.

Read image winners (Skill 1) and concepts (Skill 2) from Supabase.
Generate 20 × 500-word JSON image prompts. Save to Supabase and markdown.

Usage:
    python3 skill3_ad_image_writer.py --account profitable_tradie --funnel labour_calc --week 2026-03-10
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
    """Extract text between start_tag and end_tag."""
    pattern = re.compile(
        re.escape(start_tag) + r"(.*?)" + re.escape(end_tag),
        re.DOTALL,
    )
    m = pattern.search(text)
    return m.group(1).strip() if m else ""


def _extract_field(block: str, field: str) -> str:
    """Extract a named field from a block."""
    pattern = re.compile(r"^" + re.escape(field) + r":\s*(.+)$", re.MULTILINE)
    m = pattern.search(block)
    return m.group(1).strip() if m else ""


def _extract_multiline_field(block: str, field: str) -> str:
    """Extract multi-line content after a field marker."""
    pattern = re.compile(r"^" + re.escape(field) + r":\s*\n?(.*)", re.DOTALL | re.MULTILINE)
    m = pattern.search(block)
    return m.group(1).strip() if m else ""


def parse_image_prompts(response_text: str) -> List[Dict[str, Any]]:
    """Parse PROMPT_START/PROMPT_END blocks from GPT-4o response."""
    prompts = []
    blocks = re.split(r"PROMPT_START", response_text)
    for block in blocks[1:]:
        end_idx = block.find("PROMPT_END")
        if end_idx != -1:
            block = block[:end_idx]

        image_id = _extract_field(block, "IMAGE_ID")
        paired_hook = _extract_field(block, "PAIRED_HOOK")
        fmt = _extract_field(block, "FORMAT")
        prompt_text = _extract_multiline_field(block, "PROMPT")

        if not image_id:
            continue

        # Parse the image_id to extract components
        # Expected format: {concept_id}_{body_ref}_H{i}_IMG_{A|B}
        parts = image_id.rsplit("_", 2)  # split off last two parts: IMG and A/B
        image_option = parts[-1] if len(parts) >= 1 else ""
        # concept_id_body_Hi part
        remainder = "_".join(parts[:-2]) if len(parts) >= 3 else image_id
        # Extract hook index
        hook_match = re.search(r"_H(\d+)$", remainder)
        hook_index = int(hook_match.group(1)) if hook_match else 0
        remainder_no_hook = remainder[: hook_match.start()] if hook_match else remainder
        # body_ref is the last single letter before _H
        body_ref_match = re.search(r"_(A|B)$", remainder_no_hook)
        body_ref = body_ref_match.group(1) if body_ref_match else ""
        concept_id = (
            remainder_no_hook[: body_ref_match.start()]
            if body_ref_match
            else remainder_no_hook
        )

        # Determine hook type from image_id (we'll look it up later from context)
        prompts.append({
            "image_id": image_id,
            "concept_id": concept_id,
            "body_ref": body_ref,
            "hook_index": hook_index,
            "image_option": image_option,
            "paired_hook_text": paired_hook,
            "image_format": fmt,
            "json_prompt": prompt_text,
            "hook_type": "",  # filled in after matching
        })

    return prompts


# ─── PROMPT BUILDER ──────────────────────────────────────────────────────────

# Neutral visual-style names (used in prompts — no social-platform references)
_FORMAT_NEUTRAL = {
    "reddit-screenshot":   "community-discussion-card",
    "forum-screenshot":    "community-discussion-card",
    "whiteboard":          "whiteboard-scene",
    "site-candid":         "on-location-photo",
    "candid":              "on-location-photo",
    "meme":                "image-with-text-overlay",
    "phone-screenshot":    "phone-screen-graphic",
    "infographic":         "informational-graphic",
    "split-panel":         "split-panel-comparison",
    "testimonial":         "quote-card",
}


def _neutral_format(raw: str) -> str:
    """Map raw format name to a neutral visual-style name."""
    return _FORMAT_NEUTRAL.get(raw.lower().strip(), raw)


def _build_flat_variants(concepts_data: list) -> list:
    """
    Flatten concepts → body copies → hooks into a list of variant dicts.
    Returns list of dicts with variant_id, concept_id, body_ref, hook_index, hook_type, hook_text, body_copy.
    """
    flat = []
    for c in concepts_data:
        concept_id = c.get("concept_id", "")
        hooks_a = c.get("hooks_a", [])
        hooks_b = c.get("hooks_b", [])
        if isinstance(hooks_a, str):
            import json as _json
            hooks_a = _json.loads(hooks_a)
        if isinstance(hooks_b, str):
            import json as _json
            hooks_b = _json.loads(hooks_b)

        for body_ref, hooks, body_copy in [("A", hooks_a, c.get("body_a", "")), ("B", hooks_b, c.get("body_b", ""))]:
            for h in hooks:
                flat.append({
                    "variant_id": f"{concept_id}_{body_ref}_H{h['index']}",
                    "concept_id": concept_id,
                    "body_ref": body_ref,
                    "hook_index": h["index"],
                    "hook_type": h["type"],
                    "hook_text": h["text"],
                    "body_copy": body_copy,
                })
    return flat


def build_batch_prompt(
    variants_batch: list,
    image_winners: list,
) -> str:
    """
    Build a GPT-4o prompt for a batch of up to 5 variants.
    Framed as visual direction for photographers/digital artists — no ad/social-media language.
    Each variant gets 2 image descriptions (Option A + Option B), 500+ words each.
    """
    winners_text = ""
    for img in image_winners[:3]:
        fmt = _neutral_format(img.get("image_format", "photo"))
        # Truncate text_on_image (can be huge) and strip any profanity/flagging content
        raw_text = img.get("text_on_image", "none") or "none"
        # Remove profanity variants that may trigger content filters
        import re as _re
        raw_text = _re.sub(r"f['\*]?n\b|f[\*]+|f\*\*k", "---", raw_text, flags=_re.IGNORECASE)
        text_shown = raw_text[:120].strip()
        if len(raw_text) > 120:
            text_shown += "..."
        winners_text += (
            f"REFERENCE #{img.get('rank')} | STYLE: {fmt}\n"
            f"Text shown: {text_shown}\n"
            f"Setting: {img.get('setting', '')}\n"
            f"Visual notes: {img.get('core_visual_claim', '')}\n\n"
        )

    top_fmt = _neutral_format(image_winners[0].get("image_format", "on-location-photo")) if image_winners else "on-location-photo"
    sec_fmt = _neutral_format(image_winners[1].get("image_format", "whiteboard-scene")) if len(image_winners) > 1 else "whiteboard-scene"

    briefs_text = ""
    for i, v in enumerate(variants_batch, 1):
        briefs_text += f"BRIEF {i}\nID: {v['variant_id']}\nMessage: {v['hook_text']}\n\n"

    return f"""You are a visual creative director writing detailed scene briefs for photographers and digital artists.

TOP-PERFORMING VISUAL REFERENCES (styles that have driven strong results):
{winners_text}PRIMARY STYLE: {top_fmt}
SECONDARY STYLE: {sec_fmt}

TASK: For each of the {len(variants_batch)} briefs below, write 2 detailed visual descriptions — Option A (primary style) and Option B (secondary style).

REQUIREMENTS FOR EVERY DESCRIPTION:
- Minimum 500 words. Be exhaustively specific — vague descriptions produce generic visuals.
- Include the exact Message text as the primary text element in the image.
- Use all 12 fields listed below.

REQUIRED FIELDS (include all 12 in every description):
1. visual_style — format name (on-location-photo, whiteboard-scene, split-panel-comparison, text-over-photo, phone-screen-graphic, informational-graphic, quote-card)
2. canvas — pixel dimensions and crop ratio
3. text_overlay — exact message text verbatim, font size/weight/colour, placement, background treatment
4. setting — precise location detail (specific surfaces, materials, time of day, architecture — not just "workshop")
5. props — every object visible, with specific make/colour/condition/position in frame
6. person — age range, build, trade clothing detail (brand, condition, colour), pose, expression, eye direction
7. lighting — source direction, quality (soft/harsh/dappled), colour temperature in Kelvin, shadows, highlights
8. composition — shot angle, lens focal length feel, depth of field, rule of thirds placement, negative space
9. colour_palette — 4-5 dominant hex codes with descriptive labels
10. mood — emotional tone in 2-3 words
11. negative_prompts — 5 specific things to exclude
12. generation_notes — AI model recommendation + any technical render flags

BRIEFS:
{briefs_text}
OUTPUT FORMAT (strict — must follow exactly):
PROMPT_START
IMAGE_ID: [ID from brief]_IMG_A
PAIRED_HOOK: [exact message text]
FORMAT: [visual style]
PROMPT: [500+ word description covering all 12 fields]
PROMPT_END
PROMPT_START
IMAGE_ID: [ID from brief]_IMG_B
PAIRED_HOOK: [exact message text]
FORMAT: [different visual style]
PROMPT: [500+ word description covering all 12 fields]
PROMPT_END

CRITICAL: You must complete a PROMPT_START/PROMPT_END block for EVERY brief listed above. Do not stop early. Write two blocks (IMG_A and IMG_B) per brief before moving to the next."""


# ─── MARKDOWN OUTPUT ─────────────────────────────────────────────────────────


def write_markdown(
    report_dir: str,
    funnel: str,
    week_start: str,
    account_key: str,
    image_winners: List[Dict[str, Any]],
    prompts: List[Dict[str, Any]],
) -> str:
    """Write the image brief markdown and return its path."""
    ensure_dir(report_dir)
    output_path = os.path.join(report_dir, f"image_brief_{funnel}_{week_start}.md")
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        f"# Image Brief — {account_key} / {funnel}",
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

    if image_winners:
        for img in image_winners:
            lines += [
                f"**RANK #{img.get('rank')} | CPL ${img.get('cpl', 0):.2f} | FORMAT: {img.get('image_format', '')}**",
                f"",
                f"- Text on image: {img.get('text_on_image', '')}",
                f"- Setting: {img.get('setting', '')}",
                f"- Authenticity signals: {img.get('authenticity_signals', '')}",
                f"- Core visual claim: {img.get('core_visual_claim', '')}",
                f"",
            ]
    else:
        lines += ["*(No image winners found)*", ""]

    lines += ["---", "", "## Image Prompts (20 total)", ""]

    for p in prompts:
        hook_label = p.get("hook_type", "").upper()
        lines += [
            f"### {p['image_id']}",
            f"",
            f"**Option:** {p['image_option']} | **Format:** {p['image_format']} | "
            f"**Hook type:** {hook_label}",
            f"",
            f"**Paired hook:**",
            f"",
            f"> {p['paired_hook_text']}",
            f"",
            f"**Prompt:**",
            f"",
            f"```",
            p["json_prompt"],
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
    """Run Skill 3 for the given account, funnel, and week."""
    if account_key not in ACCOUNTS:
        raise ValueError(f"Unknown account key: {account_key}")

    account = ACCOUNTS[account_key]
    client_slug = account["client_slug"]
    week_str = get_week_str(week_start)
    report_dir = account["report_dir"]

    supabase = get_supabase_client()
    openai_client = get_openai_client()

    print(f"\n{'='*60}")
    print(f"  Skill 3 — Ad Image Writer")
    print(f"  Account : {account_key}")
    print(f"  Funnel  : {funnel}")
    print(f"  Week    : {week_start} ({week_str})")
    print(f"{'='*60}")

    # ── Read Supabase data ──
    print("\n[3] Reading image winners from Supabase…")
    try:
        img_resp = (
            supabase.table("ad_image_winners")
            .select("*")
            .eq("account_id", account["account_id"])
            .eq("funnel_name", funnel)
            .eq("week_start", week_start)
            .order("rank")
            .execute()
        )
        image_winners = img_resp.data or []
    except Exception as exc:
        raise RuntimeError(f"Failed to read ad_image_winners: {exc}") from exc

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

    if not image_winners:
        raise RuntimeError("No image winners found. Run Skill 1 first.")
    if not concepts_data:
        raise RuntimeError("No concepts found. Run Skill 2 first.")

    print(f"  Image winners: {len(image_winners)}, Concepts: {len(concepts_data)}")

    # ── Flatten variants and batch into groups of 5 ──
    print("\n[3] Building variant batches (5 per GPT-4o call)…")
    flat_variants = _build_flat_variants(concepts_data)
    variant_lookup = {v["variant_id"]: v for v in flat_variants}
    batch_size = 2
    batches = [flat_variants[i:i + batch_size] for i in range(0, len(flat_variants), batch_size)]
    print(f"  {len(flat_variants)} variants → {len(batches)} batch(es)")

    # ── Call GPT-4o per batch ──
    all_prompts = []
    for batch_num, batch in enumerate(batches, 1):
        print(f"[3] Batch {batch_num}/{len(batches)}: {len(batch)} variant(s)…")
        prompt = build_batch_prompt(batch, image_winners)
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=16000,
                temperature=0.7,
            )
            response_text = response.choices[0].message.content or ""
        except Exception as exc:
            print(f"  [ERROR] GPT-4o call failed for batch {batch_num}: {exc}")
            continue

        batch_prompts = parse_image_prompts(response_text)
        print(f"  Batch {batch_num}: parsed {len(batch_prompts)} prompt(s)")

        # Fill in hook_type from lookup
        for p in batch_prompts:
            base_variant = p["image_id"].rsplit("_IMG_", 1)[0]
            if base_variant in variant_lookup:
                p["hook_type"] = variant_lookup[base_variant].get("hook_type", "")

        all_prompts.extend(batch_prompts)

    prompts = all_prompts
    print(f"  Total parsed across all batches: {len(prompts)} image prompt(s).")

    # ── Save to Supabase ──
    for p in prompts:
        image_id = p["image_id"]
        row = {
            "image_id": image_id,
            "account_id": account["account_id"],
            "funnel_name": funnel,
            "week_start": week_start,
            "concept_id": p["concept_id"],
            "body_ref": p["body_ref"],
            "hook_index": p["hook_index"],
            "hook_type": p["hook_type"],
            "image_option": p["image_option"],
            "paired_hook_text": p["paired_hook_text"],
            "json_prompt": p["json_prompt"],
            "image_format": p["image_format"],
        }
        try:
            supabase.table("ad_images").upsert(row, on_conflict="image_id").execute()
            print(f"  [DB] Upserted ad_images: {image_id}")
        except Exception as exc:
            print(f"  [ERROR] Supabase upsert failed for {image_id}: {exc}")

    # ── Write markdown ──
    write_markdown(report_dir, funnel, week_start, account_key, image_winners, prompts)

    print(f"\n{'='*60}")
    print(f"  Skill 3 COMPLETE — {len(prompts)} image prompt(s) generated.")
    print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Skill 3 — Ad Image Writer")
    parser.add_argument("--account", required=True, help="Account key (e.g. profitable_tradie)")
    parser.add_argument("--funnel", required=True, help="Funnel key (e.g. labour_calc)")
    parser.add_argument("--week", required=True, help="Week start date YYYY-MM-DD")
    args = parser.parse_args()
    run(args.account, args.funnel, args.week)

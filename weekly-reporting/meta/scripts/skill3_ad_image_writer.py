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


def _build_variants_section(concepts_data: List[Dict[str, Any]]) -> Tuple[str, List[Dict]]:
    """
    Build the AD VARIANTS section of the prompt.
    Returns (variants_text, flat_variant_list).
    """
    lines = []
    flat_variants = []

    for c in concepts_data:
        concept_id = c.get("concept_id", "")
        hooks_a = json.loads(c.get("hooks_a", "[]")) if isinstance(c.get("hooks_a"), str) else (c.get("hooks_a") or [])
        hooks_b = json.loads(c.get("hooks_b", "[]")) if isinstance(c.get("hooks_b"), str) else (c.get("hooks_b") or [])

        for body_ref, hooks, body_copy in [("A", hooks_a, c.get("body_a", "")), ("B", hooks_b, c.get("body_b", ""))]:
            for h in hooks:
                variant_id = f"{concept_id}_{body_ref}_H{h['index']}"
                lines += [
                    f"VARIANT: {variant_id}",
                    f"Hook type: {h['type']}",
                    f"Hook text: {h['text']}",
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
                })

    return "\n".join(lines), flat_variants


def build_prompt(
    image_winners: List[Dict[str, Any]],
    concepts_data: List[Dict[str, Any]],
) -> Tuple[str, List[Dict]]:
    """Build the GPT-4o prompt for image prompt generation."""

    winners_section = ""
    for img in image_winners:
        winners_section += (
            f"RANK #{img.get('rank')} | CPL ${img.get('cpl', 0):.2f} | "
            f"FORMAT: {img.get('image_format', 'unknown')}\n"
            f"Text on image: {img.get('text_on_image', '')}\n"
            f"Setting: {img.get('setting', '')}\n"
            f"Authenticity signals: {img.get('authenticity_signals', '')}\n"
            f"Core visual claim: {img.get('core_visual_claim', '')}\n\n"
        )

    winning_format = image_winners[0].get("image_format", "reddit-screenshot") if image_winners else "reddit-screenshot"
    second_format = image_winners[1].get("image_format", "whiteboard") if len(image_winners) > 1 else "whiteboard"

    variants_section, flat_variants = _build_variants_section(concepts_data)

    prompt = f"""You are an expert AI image prompt writer for Facebook/Instagram ads.
Your prompts are used directly by AI image generators (Gemini, DALL-E 3). They must be long, specific, and visually unambiguous.

MINIMUM LENGTH RULE: Every PROMPT field must be 500+ words. No exceptions.
SHORT PROMPTS FAIL. Vague prompts produce generic images. Specific prompts produce winning ads.

TOP PERFORMING IMAGE ADS (what's working — all time):
{winners_section}
WINNING FORMAT: {winning_format} (from Rank #1 — use as Image Option A base)
SECOND FORMAT: {second_format} (use as Image Option B base)

Generate 20 image prompts — one for each ad variant below.
For each variant, write 2 prompts (Option A and Option B).
Option A = based on the winning format.
Option B = different format, same hook story.

HOOK ALIGNMENT RULE: When text appears in the image (Reddit headline, whiteboard message, sticky note, etc.), it MUST use the exact paired hook language word-for-word.

MANDATORY FIELDS IN EVERY PROMPT (all must be present, all must be detailed):
1. format — specific name (reddit-screenshot, whiteboard, phone-screenshot, split-panel, site-candid, meme)
2. platform — canvas dimensions and placement (e.g. "Facebook/Instagram feed, 1:1 1080×1080px")
3. exact_text — every word of text that appears in the image, verbatim from the hook
4. text_placement — where on the canvas text appears, font size, weight, colour
5. setting — specific location (not "office" — "a weathered timber workshop bench with metal shavings and a yellow Dewalt drill visible")
6. props — every object in frame, specific brand/colour/condition
7. person_description — age, build, trade clothing (stubby shorts, hi-vis, work boots), expression, pose, whether looking at camera
8. lighting — direction, quality, colour temperature, time of day
9. composition — shot angle (eye-level, slightly below, overhead), focal length feel, depth of field
10. colour_palette — 3-5 hex codes that dominate the image
11. authenticity_signals — what makes this look like a real business owner's photo (cluttered background, worn tools, slightly overexposed, candid mid-action)
12. what_to_avoid — at least 5 specific things (stock photo backgrounds, perfect symmetry, models with makeup, brand logos, white clean studios, etc.)
13. ai_model_note — "Gemini 1.5 Pro for photorealistic" OR "DALL-E 3 for graphic/meme"

EXAMPLE OF A CORRECT 500-WORD PROMPT (use this as your template):
{{
  "format": "forum-style-graphic",
  "platform": "Facebook/Instagram feed, 1:1 square, 1080x1080px",
  "concept": "Ad creative styled as an organic community discussion post — a format that performs well because it mirrors real tradespeople sharing authentic experiences.",
  "exact_text": "Worked 237 days straight. Still barely breaking even. Here's what nobody tells you about trade pricing.",
  "text_placement": {{
    "community_label": "Fictional branded community label — top left, 11pt sans-serif, #888888 — e.g. 'Trades Business Owners Group'",
    "username": "Fictional first-person name + trade — e.g. 'Pete — Sparky, Brisbane' — same line, grey, 11pt",
    "headline_text": "Worked 237 days straight. Still barely breaking even. Here's what nobody tells you about trade pricing. — 26pt bold, #1A1A1B, spans full card width",
    "body_preview": "Two lines of body text — first-person personal story tone — 13pt regular, #3C3C3C",
    "engagement_bar": "Reaction count + comment count + share link — 12pt, grey tones, bottom of card"
  }},
  "card_design": {{
    "card_background": "#FFFFFF white card",
    "outer_background": "#1A1A1B dark background as 16px border all sides",
    "corner_radius": "8px rounded corners on card",
    "drop_shadow": "Subtle 2px shadow, 10% black opacity, softens card edge"
  }},
  "setting": "Digital graphic only. The card fills 88% of the canvas. Dark outer background shows on all four sides. No real-world photography in this format variant.",
  "props": "No physical props. Interface-style elements only: text blocks, fictional community name, fictional first-person username, reaction icon row, comment count. All fictional — no impersonation of real platforms.",
  "person_description": "No person visible. The copy carries all human voice. The fictional username implies a real person behind the post without showing one.",
  "lighting": "Flat digital render — no photography lighting. White card, no internal shadows. Clean and minimal.",
  "composition": "Perfectly centred card on dark outer background. Zero angle or perspective. Straight-on flat view. Equal margins all four sides. 1:1 locked.",
  "colour_palette": [
    "#FFFFFF — card background",
    "#1A1A1B — outer wrap and headline text",
    "#888888 — meta text (community label, username, timestamp)",
    "#3C3C3C — body copy text",
    "#E5E5E5 — subtle card border stroke"
  ],
  "authenticity_signals": [
    "Fictional username reads as a real individual tradesperson — not a brand or company name",
    "Community label is clearly a branded group name — not impersonating any real social platform by name",
    "Reaction count in hundreds or thousands — implies strong social traction",
    "Timestamp shows recent post — e.g. 'posted 6 hours ago'",
    "Body text starts mid-personal-story — first person, specific number, honest frustration or insight",
    "No logos, brand colours, or corporate elements inside the card"
  ],
  "what_to_avoid": [
    "Any angled or perspective view — must be flat and straight-on",
    "Naming or visually referencing any real social platform (Reddit, Facebook, Twitter, etc.)",
    "Stock photography or illustrations inside the card area",
    "Corporate brand colours, gradients, or professional design polish inside the card",
    "Any real platform logos, trademarks, or UI elements",
    "Perfect visual symmetry that reads as designed rather than organic",
    "Generic business stock imagery"
  ],
  "ai_model_note": "DALL-E 3 for precise text rendering in UI-style graphics. Generate as flat 2D digital mockup at 1080x1080px. This is a graphic design, not a photograph."
}}

AD VARIANTS:
{variants_section}
For each variant, output:
PROMPT_START
IMAGE_ID: {{concept_id}}_{{body_ref}}_H{{i}}_IMG_A
PAIRED_HOOK: [exact hook text]
FORMAT: [format name]
PROMPT: [500+ word JSON prompt with ALL 13 mandatory fields — use the example above as your template length and detail level]
PROMPT_END
PROMPT_START
IMAGE_ID: {{concept_id}}_{{body_ref}}_H{{i}}_IMG_B
PAIRED_HOOK: [same hook text]
FORMAT: [different format]
PROMPT: [500+ word JSON prompt with ALL 13 mandatory fields]
PROMPT_END"""

    return prompt, flat_variants


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

    # ── Build prompt ──
    print("\n[3] Building GPT-4o prompt…")
    prompt, flat_variants = build_prompt(image_winners, concepts_data)

    # ── Call GPT-4o ──
    print("[3] Calling GPT-4o for image prompt generation…")
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
    prompts = parse_image_prompts(response_text)
    print(f"  Parsed {len(prompts)} image prompt(s).")

    # Fill in hook_type from flat_variants lookup
    variant_lookup = {v["variant_id"]: v for v in flat_variants}
    for p in prompts:
        base_variant = p["image_id"].rsplit("_IMG_", 1)[0]
        if base_variant in variant_lookup:
            p["hook_type"] = variant_lookup[base_variant].get("hook_type", "")

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

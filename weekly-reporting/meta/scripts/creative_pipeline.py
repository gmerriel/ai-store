"""
creative_pipeline.py — Orchestrator for the Creative Intelligence Pipeline.

Runs all 4 skills in sequence for one or all accounts/funnels, then produces
a master Creative Brief per funnel organized by VARIANT (not by skill).

Usage:
    python3 creative_pipeline.py --account profitable_tradie --week 2026-03-10
    python3 creative_pipeline.py --account all --week 2026-03-10
"""

import argparse
import json
import os
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

from creative_config import (
    ACCOUNTS,
    ensure_dir,
    get_supabase_client,
    get_week_str,
)

# Import skill runners
import skill1_winner_extraction as skill1
import skill2_ad_copy_writer as skill2
import skill3_ad_image_writer as skill3
import skill4_ad_video_writer as skill4


# ─── MASTER BRIEF BUILDER ────────────────────────────────────────────────────


def _load_markdown(path: str) -> str:
    """Load a markdown file's content, or return empty string."""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def _extract_variant_sections_copy(copy_md: str) -> Dict[str, Dict[str, str]]:
    """
    Extract per-variant hook + body sections from the copy brief markdown.

    Returns:
        Dict keyed by variant_id → {hook_text, body, hook_type}
    """
    # This is a best-effort extraction from the structured markdown
    variants: Dict[str, Dict[str, str]] = {}
    current_concept = ""
    current_body = ""
    current_hook_key = ""
    buffer = []

    for line in copy_md.split("\n"):
        # Concept heading
        if line.startswith("### Concept"):
            current_concept = line.replace("### Concept", "").strip().split(":")[0].strip()
        # Body heading
        if "#### Body A" in line:
            current_body = "A"
        elif "#### Body B" in line:
            current_body = "B"
        # Hook heading — e.g. **Hook A1 [CONTINUER]** (10 words)
        if line.startswith("**Hook") and "[" in line and "]" in line:
            # Extract hook index and type
            import re
            m = re.search(r"Hook\s+([AB])(\d+)\s+\[(\w+)\]", line)
            if m and current_concept:
                body_ref = m.group(1)
                hook_idx = m.group(2)
                hook_type = m.group(3).lower()
                current_hook_key = f"{current_concept}_{body_ref}_H{hook_idx}"
                variants[current_hook_key] = {"hook_type": hook_type, "hook_text": "", "body_copy": ""}
        # Hook text is inside blockquote
        if line.startswith("> ") and current_hook_key:
            variants[current_hook_key]["hook_text"] = line[2:].strip()

    return variants


def build_master_brief(
    account_key: str,
    funnel: str,
    week_start: str,
    report_dir: str,
) -> str:
    """
    Combine copy + image + video briefs into one master Creative Brief
    organized by VARIANT (concept → body → hook).

    Returns path to master brief file.
    """
    ensure_dir(report_dir)
    output_path = os.path.join(report_dir, f"creative_brief_{funnel}_{week_start}.md")
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    supabase = get_supabase_client()
    account = ACCOUNTS[account_key]
    account_id = account["account_id"]
    week_str = get_week_str(week_start)

    print(f"\n[PIPELINE] Building master creative brief for {account_key} / {funnel}…")

    # Load all data from Supabase
    try:
        concepts_resp = (
            supabase.table("ad_concepts")
            .select("*")
            .eq("account_id", account_id)
            .eq("funnel_name", funnel)
            .eq("week_start", week_start)
            .execute()
        )
        concepts = concepts_resp.data or []
    except Exception as exc:
        print(f"  [WARN] Could not load concepts: {exc}")
        concepts = []

    try:
        images_resp = (
            supabase.table("ad_images")
            .select("*")
            .eq("account_id", account_id)
            .eq("funnel_name", funnel)
            .eq("week_start", week_start)
            .execute()
        )
        images = images_resp.data or []
    except Exception as exc:
        print(f"  [WARN] Could not load ad_images: {exc}")
        images = []

    try:
        scripts_resp = (
            supabase.table("ad_video_scripts")
            .select("*")
            .eq("account_id", account_id)
            .eq("funnel_name", funnel)
            .eq("week_start", week_start)
            .execute()
        )
        scripts = scripts_resp.data or []
    except Exception as exc:
        print(f"  [WARN] Could not load ad_video_scripts: {exc}")
        scripts = []

    # Build lookups
    # images_by_variant: variant_base → {A: row, B: row}
    images_by_variant: Dict[str, Dict[str, Any]] = {}
    for img in images:
        image_id = img.get("image_id", "")
        # Strip _IMG_A or _IMG_B suffix
        base = image_id.rsplit("_IMG_", 1)[0] if "_IMG_" in image_id else image_id
        option = img.get("image_option", "A")
        if base not in images_by_variant:
            images_by_variant[base] = {}
        images_by_variant[base][option] = img

    # scripts_by_variant: variant_base → row
    scripts_by_variant: Dict[str, Any] = {}
    for s in scripts:
        script_id = s.get("script_id", "")
        base = script_id.replace("_VID", "") if script_id.endswith("_VID") else script_id
        scripts_by_variant[base] = s

    lines = [
        f"# Master Creative Brief — {account_key} / {funnel}",
        f"",
        f"**Generated:** {timestamp}  ",
        f"**Week:** {week_start}  ",
        f"**Account:** {account_key}  ",
        f"**Funnel:** {funnel}  ",
        f"",
        f"---",
        f"",
    ]

    for c in concepts:
        concept_id = c.get("concept_id", "")
        concept_num = c.get("concept_num", "?")
        concept_name = c.get("concept_name", "")
        inspired_by = c.get("inspired_by", "")
        headline = c.get("headline", "")

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

        lines += [
            f"## CONCEPT C{concept_num}: {concept_name}",
            f"",
            f"**Headline:** {headline}  ",
            f"**Inspired by:** {inspired_by}",
            f"",
        ]

        for body_ref, hooks, body_copy in [
            ("A", hooks_a, c.get("body_a", "")),
            ("B", hooks_b, c.get("body_b", "")),
        ]:
            lines += [
                f"### Body {body_ref}",
                f"",
                f"```",
                body_copy,
                f"```",
                f"",
            ]
            for h in hooks:
                hook_idx = h.get("index", 0)
                hook_type = h.get("type", "").upper()
                hook_text = h.get("text", "")
                word_count = h.get("word_count", 0)
                variant_id = f"{concept_id}_{body_ref}_H{hook_idx}"

                lines += [
                    f"#### VARIANT {variant_id} — [{hook_type}] ({word_count} words)",
                    f"",
                    f"**COPY — Hook:**",
                    f"",
                    f"> {hook_text}",
                    f"",
                ]

                # Image prompts
                img_variants = images_by_variant.get(variant_id, {})
                for opt in ("A", "B"):
                    img = img_variants.get(opt)
                    if img:
                        lines += [
                            f"**IMAGE {opt} — {img.get('image_format', '')}:**",
                            f"",
                            f"```",
                            img.get("json_prompt", "(no prompt)"),
                            f"```",
                            f"",
                        ]
                    else:
                        lines += [f"**IMAGE {opt}:** *(not generated)*", f""]

                # Video script
                vid = scripts_by_variant.get(variant_id)
                if vid:
                    action_flag = " ⚠️" if not vid.get("action_valid", True) else ""
                    lines += [
                        f"**VIDEO SCRIPT{action_flag}:**",
                        f"",
                        f"| | |",
                        f"|---|---|",
                        f"| **Location** | {vid.get('location', '')} |",
                        f"| **Prop** | {vid.get('prop', '')} |",
                        f"| **Action** | {vid.get('action', '')} |",
                        f"| **Energy** | {vid.get('energy', '')} | ~{vid.get('estimated_seconds', '?')}s |",
                        f"",
                        f"```",
                        vid.get("full_script", "(no script)"),
                        f"```",
                        f"",
                    ]
                    if vid.get("action_warning"):
                        lines += [f"> {vid['action_warning']}", f""]
                else:
                    lines += [f"**VIDEO SCRIPT:** *(not generated)*", f""]

                lines += ["---", ""]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  [MD] Master brief written: {output_path}")
    return output_path


# ─── PIPELINE RUNNER ─────────────────────────────────────────────────────────


def run_account(account_key: str, week_start: str) -> Dict[str, Any]:
    """Run the full pipeline for one account. Returns a summary dict."""
    account = ACCOUNTS[account_key]
    report_dir = account["report_dir"]

    summary: Dict[str, Any] = {
        "account": account_key,
        "week": week_start,
        "skill1": "pending",
        "funnels": {},
    }

    print(f"\n{'#'*60}")
    print(f"  PIPELINE START — {account_key} / {week_start}")
    print(f"{'#'*60}")

    # ── Skill 1 (account-wide) ──
    print(f"\n>>> STEP 1: Skill 1 — Winner Extraction")
    try:
        skill1.run(account_key, week_start)
        summary["skill1"] = "ok"
    except Exception as exc:
        summary["skill1"] = f"error: {exc}"
        print(f"  [ERROR] Skill 1 failed: {exc}")
        traceback.print_exc()

    # ── Discover funnels from Supabase (auto-detected by Skill 1) ──
    supabase = get_supabase_client()
    r = supabase.table("ad_copy_winners").select("funnel_name").eq(
        "week_start", week_start
    ).neq("funnel_name", "unknown").execute()
    funnels = sorted({row["funnel_name"] for row in r.data})
    print(f"\n  Funnels detected by Skill 1: {funnels}")

    # ── Skills 2-4 per funnel ──
    for funnel in funnels:
        print(f"\n>>> FUNNEL: {funnel}")
        funnel_summary: Dict[str, str] = {}

        # Skill 2
        print(f"  STEP 2: Skill 2 — Copy Writer")
        try:
            skill2.run(account_key, funnel, week_start)
            funnel_summary["skill2"] = "ok"
        except Exception as exc:
            funnel_summary["skill2"] = f"error: {exc}"
            print(f"  [ERROR] Skill 2 failed for {funnel}: {exc}")
            traceback.print_exc()

        # Skill 3
        print(f"  STEP 3: Skill 3 — Image Writer")
        try:
            skill3.run(account_key, funnel, week_start)
            funnel_summary["skill3"] = "ok"
        except Exception as exc:
            funnel_summary["skill3"] = f"error: {exc}"
            print(f"  [ERROR] Skill 3 failed for {funnel}: {exc}")
            traceback.print_exc()

        # Skill 4
        print(f"  STEP 4: Skill 4 — Video Writer")
        try:
            skill4.run(account_key, funnel, week_start)
            funnel_summary["skill4"] = "ok"
        except Exception as exc:
            funnel_summary["skill4"] = f"error: {exc}"
            print(f"  [ERROR] Skill 4 failed for {funnel}: {exc}")
            traceback.print_exc()

        # Master brief
        print(f"  STEP 5: Building master creative brief…")
        try:
            brief_path = build_master_brief(account_key, funnel, week_start, report_dir)
            funnel_summary["master_brief"] = brief_path
        except Exception as exc:
            funnel_summary["master_brief"] = f"error: {exc}"
            print(f"  [ERROR] Master brief failed for {funnel}: {exc}")
            traceback.print_exc()

        summary["funnels"][funnel] = funnel_summary

    return summary


def print_summary(summaries: List[Dict[str, Any]]) -> None:
    """Print a human-readable run summary."""
    print(f"\n{'='*60}")
    print(f"  PIPELINE SUMMARY")
    print(f"{'='*60}")
    for s in summaries:
        print(f"\n  Account : {s['account']} | Week: {s['week']}")
        print(f"  Skill 1 : {s['skill1']}")
        for funnel, fs in s.get("funnels", {}).items():
            status_parts = [
                f"S2:{fs.get('skill2', '-')}",
                f"S3:{fs.get('skill3', '-')}",
                f"S4:{fs.get('skill4', '-')}",
            ]
            brief = fs.get("master_brief", "")
            brief_str = "ok" if brief and not brief.startswith("error") else brief
            print(f"    {funnel}: {' | '.join(status_parts)} | Brief:{brief_str}")
    print(f"\n{'='*60}")


# ─── MAIN ────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Creative Intelligence Pipeline Orchestrator")
    parser.add_argument(
        "--account",
        required=True,
        help="Account key (e.g. profitable_tradie) or 'all' to run all accounts",
    )
    parser.add_argument("--week", required=True, help="Week start date YYYY-MM-DD")
    args = parser.parse_args()

    if args.account == "all":
        account_keys = list(ACCOUNTS.keys())
    else:
        if args.account not in ACCOUNTS:
            raise ValueError(
                f"Unknown account '{args.account}'. Available: {list(ACCOUNTS.keys())}"
            )
        account_keys = [args.account]

    summaries = []
    for account_key in account_keys:
        s = run_account(account_key, args.week)
        summaries.append(s)

    print_summary(summaries)


if __name__ == "__main__":
    main()

"""
skill1_winner_extraction.py — Phase 1 of the Creative Intelligence Pipeline.

Pull all-time top-performing ads from Meta, transcribe videos with Whisper,
analyse images with GPT-4o Vision. Save winners to Supabase.

Winner selection logic:
  - Deduplicates by creative_id — same creative across multiple campaigns/adsets is aggregated
  - Relative spend threshold: creative must account for ≥ 2% of funnel total spend (scales with account size)
  - Winner score = conversions × (funnel_avg_cpl / creative_cpl)
    → rewards both conversion volume AND efficiency vs. the funnel's own benchmark

Usage:
    python3 skill1_winner_extraction.py --account profitable_tradie --week 2026-03-10
"""

import argparse
import base64
import json
import os
import subprocess
import time
from typing import Any, Dict, List, Optional, Set, Tuple

import requests  # type: ignore

from creative_config import (
    ACCOUNTS,
    META_BASE,
    META_TOKEN,
    ensure_dir,
    get_openai_client,
    get_supabase_client,
    get_week_str,
)

# ─── CONSTANTS ────────────────────────────────────────────────────────────────

LEAD_ACTION_TYPES = {
    "lead",
    "offsite_conversion.fb_pixel_lead",
    "omni_complete_registration",
}

# Relative spend threshold: creative must be ≥ this share of funnel total spend.
# Scales automatically: $3k/month account → 2% = $60 floor; $3.5M/month → $70k floor.
MIN_SPEND_SHARE = 0.02

# Absolute floor — safety net for very new or tiny accounts.
MIN_SPEND_FLOOR = 50.0

# Number of winners to surface per funnel per asset type.
TOP_N = 5

WORKSPACE_DIR = "/Users/atlas/.openclaw/workspace"


# ─── HELPERS ─────────────────────────────────────────────────────────────────


def _meta_get(url: str, params: Dict[str, Any], retries: int = 3) -> Dict[str, Any]:
    """GET a Meta Graph API endpoint with retry on transient errors."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code in (400, 500, 502, 503, 504) and attempt < retries - 1:
                print(f"    [WARN] HTTP {resp.status_code} — retrying in 30s…")
                time.sleep(30)
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            if attempt < retries - 1:
                print(f"    [WARN] Request error: {exc} — retrying in 30s…")
                time.sleep(30)
            else:
                raise
    return {}


def _compute_conversions(ad: Dict[str, Any]) -> int:
    """Sum qualifying conversion actions from an ad insights row."""
    actions = ad.get("actions") or []
    return sum(
        int(float(a.get("value", 0)))
        for a in actions
        if a.get("action_type") in LEAD_ACTION_TYPES
    )


def _detect_funnel(url: str, funnels: Dict[str, Any]) -> str:
    """Match a destination URL against funnel base_url_contains keys."""
    clean = url.split("?")[0].lower()
    for funnel_key, funnel_cfg in funnels.items():
        if funnel_cfg["base_url_contains"].lower() in clean:
            return funnel_key
    return "unknown"


def _get_dest_url(story_spec: Dict[str, Any]) -> str:
    """Extract destination URL from object_story_spec."""
    try:
        return story_spec["link_data"]["link"]
    except (KeyError, TypeError):
        pass
    try:
        return story_spec["video_data"]["call_to_action"]["value"]["link"]
    except (KeyError, TypeError):
        pass
    return ""


# ─── PHASE 1A — CREATIVE WINNER RANKING ──────────────────────────────────────


def phase_1a(account: Dict[str, Any], week_start: str, week_str: str) -> Dict[str, List[Dict]]:
    """
    Pull all-time ad insights, deduplicate by creative_id, score, rank winners.

    Winner score = conversions × (funnel_avg_cpl / creative_cpl)
    Threshold = max(2% of funnel spend, $50 absolute floor)

    Returns:
        Dict keyed by funnel name → list of winner creative records (image + video combined).
    """
    account_id_raw = account["account_id"]
    client_slug = account["client_slug"]
    funnels = account["funnels"]
    supabase = get_supabase_client()

    # ── Step 1: Fetch all ad insights (all-time) ──────────────────────────────
    print("\n[1A] Fetching all-time ad insights from Meta…")
    all_insights: List[Dict] = []
    url = f"{META_BASE}/{account_id_raw}/insights"
    params = {
        "date_preset": "maximum",
        "level": "ad",
        "fields": "ad_id,ad_name,spend,actions",
        "limit": 500,
        "access_token": META_TOKEN,
    }
    page = 0
    while True:
        page += 1
        print(f"  Fetching insights page {page}…")
        try:
            data = _meta_get(url, params)
        except Exception as exc:
            print(f"  [ERROR] Insights fetch failed on page {page}: {exc}")
            break
        all_insights.extend(data.get("data", []))
        time.sleep(0.5)
        next_url = data.get("paging", {}).get("next")
        if not next_url:
            break
        url = next_url
        params = {}

    print(f"  Total insight rows: {len(all_insights)}")

    # ── Step 2: Quick pre-filter (absolute floor only — real threshold comes after aggregation) ──
    # Only skip truly zero-spend ads to avoid unnecessary creative API calls.
    pre_qualified: List[Dict] = []
    for row in all_insights:
        spend = float(row.get("spend", 0))
        if spend < MIN_SPEND_FLOOR:
            continue
        conversions = _compute_conversions(row)
        if conversions == 0:
            continue
        row["_spend"] = spend
        row["_conversions"] = conversions
        pre_qualified.append(row)

    print(f"  Ads passing absolute floor (spend≥${MIN_SPEND_FLOOR}, conversions≥1): {len(pre_qualified)}")

    # ── Step 3: Fetch creative data for each pre-qualified ad ─────────────────
    # We need creative_id (to deduplicate), asset_type, funnel URL, and creative copy.
    print("  Fetching creative metadata per ad…")
    creative_map: Dict[str, Dict] = {}  # ad_id → creative metadata

    for idx, ad in enumerate(pre_qualified):
        ad_id = ad["ad_id"]
        time.sleep(0.4)
        try:
            result = _meta_get(
                f"{META_BASE}/{ad_id}",
                {
                    "fields": "creative{id,body,title,object_story_spec,video_id,image_url,thumbnail_url}",
                    "access_token": META_TOKEN,
                },
            )
        except Exception as exc:
            print(f"  [WARN] Creative fetch failed for ad {ad_id}: {exc}")
            continue

        creative = result.get("creative", {})
        creative_id = creative.get("id", ad_id)  # fallback to ad_id if no creative object

        story_spec = creative.get("object_story_spec", {})
        dest_url = _get_dest_url(story_spec)
        funnel = _detect_funnel(dest_url, funnels) if dest_url else "unknown"

        creative_map[ad_id] = {
            "creative_id": creative_id,
            "asset_type": "video" if creative.get("video_id") else "image",
            "video_id": creative.get("video_id"),
            "image_url": creative.get("image_url") or creative.get("thumbnail_url", ""),
            "headline": creative.get("title", ""),
            "body_copy": creative.get("body", ""),
            "funnel": funnel,
        }

    print(f"  Creative metadata fetched for {len(creative_map)} ads.")

    # ── Step 4: Aggregate spend + conversions by (creative_id, funnel) ────────
    # Same creative running in 3 campaigns for 3 audiences → one aggregated record.
    print("  Aggregating performance by creative…")
    registry: Dict[Tuple[str, str], Dict] = {}  # (creative_id, funnel) → aggregated record

    for ad in pre_qualified:
        ad_id = ad["ad_id"]
        c = creative_map.get(ad_id)
        if not c:
            continue
        key = (c["creative_id"], c["funnel"])
        if key not in registry:
            registry[key] = {
                "creative_id": c["creative_id"],
                "funnel": c["funnel"],
                "asset_type": c["asset_type"],
                "video_id": c.get("video_id"),
                "image_url": c["image_url"],
                "headline": c["headline"],
                "body_copy": c["body_copy"],
                "total_spend": 0.0,
                "total_conversions": 0,
                "ad_ids": [],
                "ad_names": [],
            }
        rec = registry[key]
        rec["total_spend"] += ad["_spend"]
        rec["total_conversions"] += ad["_conversions"]
        rec["ad_ids"].append(ad_id)
        rec["ad_names"].append(ad.get("ad_name", ""))

    print(f"  Unique (creative × funnel) combinations: {len(registry)}")

    # ── Step 5: Calculate per-funnel benchmarks ───────────────────────────────
    # Benchmark = funnel's own total spend and avg CPL — the account's internal truth.
    funnel_benchmarks: Dict[str, Dict] = {}
    for (creative_id, funnel), rec in registry.items():
        if funnel == "unknown":
            continue
        if funnel not in funnel_benchmarks:
            funnel_benchmarks[funnel] = {"total_spend": 0.0, "total_conversions": 0}
        funnel_benchmarks[funnel]["total_spend"] += rec["total_spend"]
        funnel_benchmarks[funnel]["total_conversions"] += rec["total_conversions"]

    for funnel, bm in funnel_benchmarks.items():
        bm["avg_cpl"] = (
            bm["total_spend"] / bm["total_conversions"] if bm["total_conversions"] > 0 else 0.0
        )
        print(
            f"  Funnel benchmark [{funnel}]: "
            f"total_spend=${bm['total_spend']:,.0f} | "
            f"total_conversions={bm['total_conversions']:,} | "
            f"avg_cpl=${bm['avg_cpl']:.2f}"
        )

    # ── Step 6: Apply relative threshold + calculate winner scores ─────────────
    # Threshold: creative spend must be ≥ max(2% of funnel spend, $50 floor)
    # Winner score: conversions × (funnel_avg_cpl / creative_cpl)
    #   → $50k/4100 leads @ $12 CPL (avg=$15): score = 4100 × (15/12) = 5,125  ✅
    #   → $50/5 leads @ $10 CPL (avg=$15):     score = 5 × (15/10)   = 7.5     ✅

    funnel_buckets: Dict[str, Dict[str, List[Dict]]] = {}

    for (creative_id, funnel), rec in registry.items():
        if funnel == "unknown" or funnel not in funnel_benchmarks:
            continue

        bm = funnel_benchmarks[funnel]
        funnel_total_spend = bm["total_spend"]
        funnel_avg_cpl = bm["avg_cpl"]

        # Relative spend threshold — scales with account size
        min_spend = max(MIN_SPEND_SHARE * funnel_total_spend, MIN_SPEND_FLOOR)
        if rec["total_spend"] < min_spend:
            continue
        if rec["total_conversions"] == 0 or funnel_avg_cpl == 0:
            continue

        creative_cpl = rec["total_spend"] / rec["total_conversions"]
        # Efficiency-weighted volume score
        winner_score = rec["total_conversions"] * (funnel_avg_cpl / creative_cpl)

        rec["creative_cpl"] = round(creative_cpl, 4)
        rec["winner_score"] = round(winner_score, 4)
        # Aliases for downstream compatibility (phases 1B, 1C, master brief)
        rec["cpl"] = rec["creative_cpl"]
        rec["spend"] = rec["total_spend"]
        rec["conversions"] = rec["total_conversions"]
        rec["ad_id"] = rec["ad_ids"][0]
        rec["ad_name"] = rec["ad_names"][0] if rec["ad_names"] else ""

        if funnel not in funnel_buckets:
            funnel_buckets[funnel] = {"image": [], "video": []}
        funnel_buckets[funnel][rec["asset_type"]].append(rec)

    # ── Step 7: Rank top N per funnel per asset type ──────────────────────────
    funnel_results: Dict[str, List[Dict]] = {}

    for funnel, buckets in funnel_buckets.items():
        funnel_winners: List[Dict] = []

        for asset_type in ("image", "video"):
            sorted_creatives = sorted(
                buckets[asset_type],
                key=lambda x: -x["winner_score"],
            )[:TOP_N]

            for rank, rec in enumerate(sorted_creatives, start=1):
                winner_id = (
                    f"{client_slug}_{funnel}_{rec['asset_type']}_"
                    f"{rec['creative_id']}_{week_str}"
                )
                row = {
                    "winner_id": winner_id,
                    "account_id": account_id_raw,
                    "funnel_name": funnel,
                    "week_start": week_start,
                    "ad_id": rec["ad_id"],
                    "ad_name": rec["ad_name"],
                    "asset_type": rec["asset_type"],
                    "cpl": round(rec["creative_cpl"], 4),
                    "spend": round(rec["total_spend"], 2),
                    "conversions": rec["total_conversions"],
                    "headline": rec["headline"],
                    "body_copy": rec["body_copy"],
                    "rank": rank,
                }
                try:
                    supabase.table("ad_copy_winners").upsert(row, on_conflict="winner_id").execute()
                except Exception as exc:
                    print(f"    [ERROR] Supabase upsert failed for {winner_id}: {exc}")

                rec["rank"] = rank
                funnel_winners.append(rec)

        funnel_results[funnel] = funnel_winners

        # Print funnel summary
        print(f"\n  [WINNERS] {funnel}:")
        for w in funnel_winners:
            campaign_count = len(set(w["ad_ids"]))
            print(
                f"    #{w['rank']} [{w['asset_type']}] "
                f"creative={w['creative_id']} | "
                f"spend=${w['total_spend']:,.0f} across {campaign_count} ad(s) | "
                f"conversions={w['total_conversions']:,} | "
                f"cpl=${w['creative_cpl']:.2f} | "
                f"score={w['winner_score']:.1f}"
            )

    return funnel_results


# ─── PHASE 1B — VIDEO TRANSCRIPTION ─────────────────────────────────────────


def phase_1b(
    account: Dict[str, Any],
    funnel_results: Dict[str, List[Dict]],
    week_start: str,
    week_str: str,
) -> None:
    """Download and transcribe top video ads via OpenAI Whisper CLI."""
    account_id_raw = account["account_id"]
    client_slug = account["client_slug"]
    supabase = get_supabase_client()

    print("\n[1B] Transcribing video ads…")

    for funnel, ads in funnel_results.items():
        video_ads = [a for a in ads if a["asset_type"] == "video"]

        if not video_ads:
            print(f"  Funnel '{funnel}': no video winners to transcribe.")
            continue

        for ad_rec in video_ads:
            ad_id = ad_rec["ad_id"]
            video_id = ad_rec.get("video_id")
            if not video_id:
                continue

            print(f"  Fetching video source for ad {ad_id} (video_id={video_id})…")
            time.sleep(0.5)

            try:
                vid_data = _meta_get(
                    f"{META_BASE}/{video_id}",
                    {"fields": "source,description,length", "access_token": META_TOKEN},
                )
            except Exception as exc:
                print(f"    [ERROR] Video metadata fetch failed: {exc}")
                continue

            video_source_url = vid_data.get("source")
            if not video_source_url:
                print(f"    [WARN] No source URL for video_id={video_id}, skipping.")
                continue

            video_path = f"/tmp/vid_{ad_id}.mp4"
            print(f"    Downloading video to {video_path}…")
            try:
                with requests.get(video_source_url, stream=True, timeout=90) as r:
                    r.raise_for_status()
                    with open(video_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=65536):
                            f.write(chunk)
            except Exception as exc:
                print(f"    [ERROR] Video download failed: {exc}")
                continue

            file_size = os.path.getsize(video_path)
            if file_size < 50 * 1024:
                print(f"    [WARN] File too small ({file_size} bytes) — skipping transcription.")
                continue

            print("    Transcribing with Whisper…")
            try:
                subprocess.run(
                    [
                        "whisper",
                        video_path,
                        "--model", "base",
                        "--language", "en",
                        "--output_format", "txt",
                        "--output_dir", "/tmp/",
                    ],
                    check=True,
                    timeout=300,
                )
            except subprocess.CalledProcessError as exc:
                print(f"    [ERROR] Whisper failed: {exc}")
                continue
            except FileNotFoundError:
                print("    [ERROR] whisper CLI not found. Install: pip install openai-whisper")
                continue

            transcript_path = f"/tmp/vid_{ad_id}.txt"
            if not os.path.exists(transcript_path):
                print(f"    [WARN] Transcript file not found: {transcript_path}")
                continue

            with open(transcript_path, "r", encoding="utf-8") as f:
                transcript = f.read().strip()

            sentences = [s.strip() for s in transcript.replace("\n", " ").split(".") if s.strip()]
            hook_text = ". ".join(sentences[:2]) + ("." if len(sentences) >= 2 else "")
            hook_words = transcript.split()
            hook_first_10 = " ".join(hook_words[:10])
            word_count = len(hook_words)

            cta_keywords = ["link", "below", "free", "grab", "click", "calculator", "download"]
            cta_text = ""
            if sentences:
                last = sentences[-1]
                if any(kw in last.lower() for kw in cta_keywords):
                    cta_text = last + "."

            hook_end = len(". ".join(sentences[:2])) + 1 if len(sentences) >= 2 else 0
            cta_start = transcript.rfind(cta_text) if cta_text else len(transcript)
            body_text = transcript[hook_end:cta_start].strip()

            transcription_id = f"{client_slug}_{funnel}_vid_{ad_id}_{week_str}"
            row = {
                "transcription_id": transcription_id,
                "ad_id": ad_id,
                "account_id": account_id_raw,
                "funnel_name": funnel,
                "week_start": week_start,
                "cpl": round(ad_rec["cpl"], 4),
                "spend": round(ad_rec["spend"], 2),
                "conversions": ad_rec["conversions"],
                "rank": ad_rec.get("rank", 0),
                "hook_text": hook_text,
                "body_text": body_text,
                "cta_text": cta_text,
                "full_transcript": transcript,
                "hook_first_10": hook_first_10,
                "word_count": word_count,
            }
            try:
                supabase.table("ad_video_transcriptions").upsert(
                    row, on_conflict="transcription_id"
                ).execute()
                print(f"    [DB] Upserted ad_video_transcriptions: {transcription_id}")
            except Exception as exc:
                print(f"    [ERROR] Supabase upsert failed: {exc}")


# ─── PHASE 1C — IMAGE ANALYSIS ───────────────────────────────────────────────


def phase_1c(
    account: Dict[str, Any],
    funnel_results: Dict[str, List[Dict]],
    week_start: str,
    week_str: str,
) -> None:
    """Download image ads and analyse with GPT-4o Vision."""
    account_id_raw = account["account_id"]
    client_slug = account["client_slug"]
    supabase = get_supabase_client()
    openai_client = get_openai_client()

    print("\n[1C] Analysing image ads with GPT-4o Vision…")

    analysis_prompt = (
        "Analyse this Facebook/Instagram ad image in detail. Extract:\n"
        "1. FORMAT: overall layout type (reddit-screenshot / whiteboard / flat-lay / "
        "phone-screenshot / meme / typographic / split-panel / site-candid / other)\n"
        "2. TEXT ON IMAGE: every piece of text visible, word for word\n"
        "3. SETTING: exact environment described\n"
        "4. PROPS: every physical object visible\n"
        "5. PERSON: if visible, what parts, clothing, action\n"
        "6. COLOUR PALETTE: dominant colours\n"
        "7. AUTHENTICITY SIGNALS: what makes it look organic/native (not like an ad)\n"
        "8. CORE VISUAL CLAIM: what does this image communicate before any text is read?\n"
        "9. WHAT IS ABSENT: no branding / no studio / etc.\n\n"
        "Be specific and detailed. Output as JSON with these 9 keys."
    )

    for funnel, ads in funnel_results.items():
        image_ads = [a for a in ads if a["asset_type"] == "image"]

        if not image_ads:
            print(f"  Funnel '{funnel}': no image winners to analyse.")
            continue

        for ad_rec in image_ads:
            ad_id = ad_rec["ad_id"]
            image_url = ad_rec.get("image_url", "")
            rank = ad_rec.get("rank", 0)

            if not image_url:
                print(f"  [WARN] No image URL for ad {ad_id}, skipping.")
                continue

            local_path = os.path.join(WORKSPACE_DIR, f"{funnel}_{rank}_analysis.png")
            print(f"  Downloading image for ad {ad_id} → {local_path}…")

            try:
                resp = requests.get(image_url, timeout=30)
                resp.raise_for_status()
                with open(local_path, "wb") as f:
                    f.write(resp.content)
            except Exception as exc:
                print(f"    [ERROR] Image download failed: {exc}")
                continue

            if os.path.getsize(local_path) < 20 * 1024:
                print("    [WARN] Image too small — skipping analysis.")
                continue

            with open(local_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")

            print("    Calling GPT-4o Vision…")
            try:
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/png;base64,{b64}"},
                                },
                                {"type": "text", "text": analysis_prompt},
                            ],
                        }
                    ],
                    max_tokens=1000,
                )
            except Exception as exc:
                print(f"    [ERROR] GPT-4o Vision call failed: {exc}")
                continue

            raw_content = response.choices[0].message.content or ""

            try:
                clean = raw_content.strip()
                if clean.startswith("```"):
                    clean = "\n".join(clean.split("\n")[1:])
                    clean = clean.rsplit("```", 1)[0].strip()
                analysis = json.loads(clean)
            except json.JSONDecodeError:
                print("    [WARN] GPT-4o returned non-JSON — storing raw.")
                analysis = {"raw": raw_content}

            image_winner_id = f"{client_slug}_{funnel}_img_{ad_id}_{week_str}"
            row = {
                "image_winner_id": image_winner_id,
                "ad_id": ad_id,
                "account_id": account_id_raw,
                "funnel_name": funnel,
                "week_start": week_start,
                "cpl": round(ad_rec["cpl"], 4),
                "spend": round(ad_rec["spend"], 2),
                "conversions": ad_rec["conversions"],
                "rank": rank,
                "local_file_path": local_path,
                "image_format": analysis.get("FORMAT", ""),
                "text_on_image": str(analysis.get("TEXT ON IMAGE", "")),
                "setting": str(analysis.get("SETTING", "")),
                "props": str(analysis.get("PROPS", "")),
                "person_description": str(analysis.get("PERSON", "")),
                "colour_palette": str(analysis.get("COLOUR PALETTE", "")),
                "authenticity_signals": str(analysis.get("AUTHENTICITY SIGNALS", "")),
                "core_visual_claim": str(analysis.get("CORE VISUAL CLAIM", "")),
                "full_analysis": json.dumps(analysis),
            }
            try:
                supabase.table("ad_image_winners").upsert(
                    row, on_conflict="image_winner_id"
                ).execute()
                print(f"    [DB] Upserted ad_image_winners: {image_winner_id}")
            except Exception as exc:
                print(f"    [ERROR] Supabase upsert failed: {exc}")

            time.sleep(0.5)


# ─── MAIN ────────────────────────────────────────────────────────────────────


def run(account_key: str, week_start: str) -> None:
    """Run all three phases for the given account and week."""
    if account_key not in ACCOUNTS:
        raise ValueError(f"Unknown account: {account_key}. Available: {list(ACCOUNTS.keys())}")

    account = ACCOUNTS[account_key]
    week_str = get_week_str(week_start)
    ensure_dir(account["report_dir"])

    print(f"\n{'='*60}")
    print(f"  Skill 1 — Winner Extraction")
    print(f"  Account : {account_key}")
    print(f"  Week    : {week_start} ({week_str})")
    print(f"{'='*60}")

    funnel_results = phase_1a(account, week_start, week_str)
    phase_1b(account, funnel_results, week_start, week_str)
    phase_1c(account, funnel_results, week_start, week_str)

    total_creatives = sum(len(v) for v in funnel_results.values())
    print(f"\n{'='*60}")
    print(f"  Skill 1 COMPLETE")
    print(f"  Funnels processed  : {len(funnel_results)}")
    print(f"  Total winner creatives : {total_creatives}")
    for funnel, creatives in funnel_results.items():
        images = [c for c in creatives if c["asset_type"] == "image"]
        videos = [c for c in creatives if c["asset_type"] == "video"]
        print(f"    {funnel}: {len(images)} image(s), {len(videos)} video(s)")
    print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Skill 1 — Winner Extraction")
    parser.add_argument("--account", required=True, help="Account key (e.g. profitable_tradie)")
    parser.add_argument("--week", required=True, help="Week start date YYYY-MM-DD")
    args = parser.parse_args()
    run(args.account, args.week)

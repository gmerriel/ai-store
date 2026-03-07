"""
skill1_winner_extraction.py — Phase 1 of the Creative Intelligence Pipeline.

Pull all-time top-performing ads from Meta, transcribe videos with Whisper,
analyse images with GPT-4o Vision. Save winners to Supabase.

Usage:
    python3 skill1_winner_extraction.py --account profitable_tradie --week 2026-03-10
"""

import argparse
import base64
import json
import os
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple

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
MIN_SPEND = 50.0
MIN_CONVERSIONS = 3
TOP_N = 5

WORKSPACE_DIR = "/Users/atlas/.openclaw/workspace"

# ─── HELPERS ─────────────────────────────────────────────────────────────────


def _meta_get(url: str, params: Dict[str, Any], retries: int = 3) -> Dict[str, Any]:
    """GET a Meta Graph API endpoint with retry on 4xx/5xx."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code in (400, 500, 502, 503, 504) and attempt < retries - 1:
                print(f"    [WARN] HTTP {resp.status_code} from Meta — retrying in 30s…")
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


def _compute_cpl(ad: Dict[str, Any]) -> Tuple[float, int]:
    """Return (cpl, conversions) for an ad row; raises ValueError if not qualifying."""
    actions = ad.get("actions") or []
    conversions = sum(
        int(float(a.get("value", 0)))
        for a in actions
        if a.get("action_type") in LEAD_ACTION_TYPES
    )
    if conversions == 0:
        raise ValueError("no qualifying actions")
    spend = float(ad.get("spend", 0))
    cpl = spend / conversions
    return cpl, conversions


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


# ─── PHASE 1A — AD COPY WINNERS ──────────────────────────────────────────────


def phase_1a(account: Dict[str, Any], week_start: str, week_str: str) -> Dict[str, List[Dict]]:
    """
    Pull all-time ad insights, filter, rank by CPL, upsert to Supabase.

    Returns:
        Dict keyed by funnel name; each value is a list of qualifying ad dicts
        (image and video combined, sorted by CPL).
    """
    account_id_raw = account["account_id"]  # e.g. "act_559512967808213"
    client_slug = account["client_slug"]
    funnels = account["funnels"]

    supabase = get_supabase_client()

    print("\n[1A] Fetching all-time ad insights from Meta…")

    url = f"{META_BASE}/{account_id_raw}/insights"
    params = {
        "date_preset": "maximum",
        "level": "ad",
        "fields": "ad_id,ad_name,adset_name,campaign_name,spend,impressions,clicks,actions,cost_per_action_type",
        "limit": 500,
        "access_token": META_TOKEN,
    }

    all_ads: List[Dict[str, Any]] = []
    page = 0
    while True:
        page += 1
        print(f"  Fetching page {page}…")
        try:
            data = _meta_get(url, params)
        except Exception as exc:
            print(f"  [ERROR] Failed to fetch insights page {page}: {exc}")
            break

        all_ads.extend(data.get("data", []))
        time.sleep(0.5)

        next_url = data.get("paging", {}).get("next")
        if not next_url:
            break
        # next URL already has all params baked in
        url = next_url
        params = {}

    print(f"  Total ad rows fetched: {len(all_ads)}")

    # Filter and compute CPL
    qualifying: List[Dict[str, Any]] = []
    for ad in all_ads:
        spend = float(ad.get("spend", 0))
        if spend < MIN_SPEND:
            continue
        try:
            cpl, conversions = _compute_cpl(ad)
        except ValueError:
            continue
        if conversions < MIN_CONVERSIONS:
            continue
        ad["_cpl"] = cpl
        ad["_conversions"] = conversions
        qualifying.append(ad)

    print(f"  Qualifying ads (spend≥{MIN_SPEND}, conversions≥{MIN_CONVERSIONS}): {len(qualifying)}")

    # Pull creative for each qualifying ad
    funnel_buckets: Dict[str, Dict[str, List[Dict]]] = {}  # funnel → {image: [], video: []}

    for idx, ad in enumerate(qualifying):
        ad_id = ad["ad_id"]
        print(f"  [{idx+1}/{len(qualifying)}] Pulling creative for ad {ad_id}…")
        time.sleep(0.5)

        try:
            creative_data = _meta_get(
                f"{META_BASE}/{ad_id}",
                {
                    "fields": "creative{body,title,object_story_spec,asset_feed_spec,video_id,image_url,thumbnail_url}",
                    "access_token": META_TOKEN,
                },
            )
        except Exception as exc:
            print(f"    [ERROR] Creative fetch failed: {exc}")
            continue

        creative = creative_data.get("creative", {})
        video_id = creative.get("video_id")
        asset_type = "video" if video_id else "image"

        story_spec = creative.get("object_story_spec", {})
        dest_url = _get_dest_url(story_spec)
        funnel = _detect_funnel(dest_url, funnels) if dest_url else "unknown"

        record = {
            "ad_id": ad_id,
            "ad_name": ad.get("ad_name", ""),
            "asset_type": asset_type,
            "cpl": ad["_cpl"],
            "spend": float(ad.get("spend", 0)),
            "conversions": ad["_conversions"],
            "headline": creative.get("title", ""),
            "body_copy": creative.get("body", ""),
            "video_id": video_id,
            "image_url": creative.get("image_url") or creative.get("thumbnail_url", ""),
            "funnel": funnel,
        }

        if funnel not in funnel_buckets:
            funnel_buckets[funnel] = {"image": [], "video": []}
        funnel_buckets[funnel][asset_type].append(record)

    # Rank and upsert top 5 per funnel per asset type
    funnel_results: Dict[str, List[Dict]] = {}

    for funnel, buckets in funnel_buckets.items():
        funnel_winners: List[Dict] = []

        for asset_type in ("image", "video"):
            sorted_ads = sorted(buckets[asset_type], key=lambda x: x["cpl"])[:TOP_N]
            for rank, ad_rec in enumerate(sorted_ads, start=1):
                winner_id = f"{client_slug}_{funnel}_{ad_rec['asset_type']}_{ad_rec['ad_id']}_{week_str}"
                row = {
                    "winner_id": winner_id,
                    "account_id": account_id_raw,
                    "funnel_name": funnel,
                    "week_start": week_start,
                    "ad_id": ad_rec["ad_id"],
                    "ad_name": ad_rec["ad_name"],
                    "asset_type": ad_rec["asset_type"],
                    "cpl": round(ad_rec["cpl"], 4),
                    "spend": round(ad_rec["spend"], 2),
                    "conversions": ad_rec["conversions"],
                    "headline": ad_rec["headline"],
                    "body_copy": ad_rec["body_copy"],
                    "rank": rank,
                }
                try:
                    supabase.table("ad_copy_winners").upsert(row, on_conflict="winner_id").execute()
                    print(f"    [DB] Upserted ad_copy_winners: {winner_id}")
                except Exception as exc:
                    print(f"    [ERROR] Supabase upsert failed for {winner_id}: {exc}")

                ad_rec["rank"] = rank
                funnel_winners.append(ad_rec)

        funnel_results[funnel] = funnel_winners

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
        video_ads = sorted(
            [a for a in ads if a["asset_type"] == "video"],
            key=lambda x: x["cpl"],
        )[:TOP_N]

        if not video_ads:
            print(f"  Funnel '{funnel}': no video ads to transcribe.")
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

            print(f"    Transcribing with Whisper…")
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
                print("    [ERROR] whisper CLI not found. Install with: pip install openai-whisper")
                continue

            transcript_path = f"/tmp/vid_{ad_id}.txt"
            if not os.path.exists(transcript_path):
                print(f"    [WARN] Transcript file not found: {transcript_path}")
                continue

            with open(transcript_path, "r", encoding="utf-8") as f:
                transcript = f.read().strip()

            # Tag sections
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

            # Body = between hook and cta
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
                supabase.table("ad_video_transcriptions").upsert(row, on_conflict="transcription_id").execute()
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
        image_ads = sorted(
            [a for a in ads if a["asset_type"] == "image"],
            key=lambda x: x["cpl"],
        )[:TOP_N]

        if not image_ads:
            print(f"  Funnel '{funnel}': no image ads to analyse.")
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
                print(f"    [WARN] Image too small — skipping analysis.")
                continue

            with open(local_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")

            print(f"    Calling GPT-4o Vision…")
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

            # Try to parse JSON from the response
            try:
                # Strip markdown code fences if present
                clean = raw_content.strip()
                if clean.startswith("```"):
                    clean = "\n".join(clean.split("\n")[1:])
                    clean = clean.rsplit("```", 1)[0].strip()
                analysis = json.loads(clean)
            except json.JSONDecodeError:
                print(f"    [WARN] GPT-4o returned non-JSON — storing as raw string.")
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
                supabase.table("ad_image_winners").upsert(row, on_conflict="image_winner_id").execute()
                print(f"    [DB] Upserted ad_image_winners: {image_winner_id}")
            except Exception as exc:
                print(f"    [ERROR] Supabase upsert failed: {exc}")

            time.sleep(0.5)


# ─── MAIN ────────────────────────────────────────────────────────────────────


def run(account_key: str, week_start: str) -> None:
    """Run all three phases for the given account and week."""
    if account_key not in ACCOUNTS:
        raise ValueError(f"Unknown account key: {account_key}. Available: {list(ACCOUNTS.keys())}")

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

    total_ads = sum(len(v) for v in funnel_results.values())
    print(f"\n{'='*60}")
    print(f"  Skill 1 COMPLETE")
    print(f"  Funnels processed : {len(funnel_results)}")
    print(f"  Total winner ads  : {total_ads}")
    for funnel, ads in funnel_results.items():
        images = [a for a in ads if a["asset_type"] == "image"]
        videos = [a for a in ads if a["asset_type"] == "video"]
        print(f"    {funnel}: {len(images)} images, {len(videos)} videos")
    print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Skill 1 — Winner Extraction")
    parser.add_argument("--account", required=True, help="Account key (e.g. profitable_tradie)")
    parser.add_argument("--week", required=True, help="Week start date YYYY-MM-DD")
    args = parser.parse_args()
    run(args.account, args.week)

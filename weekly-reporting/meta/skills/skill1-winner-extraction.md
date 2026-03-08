---
name: extracting-ad-winners
description: Extracts all-time top-performing Meta ad copy, video transcriptions, and image visuals from a given ad account. Pulls written captions from image/video ads, transcribes video scripts using Whisper, and analyses top image ads using GPT-4o Vision. Saves all data to Supabase for use by downstream skills. Use when pulling creative benchmarks from a Meta ad account before generating new ads.
---

# Skill 1 — Extracting Ad Winners

Pulls all-time top-performing creative assets from a Meta ad account, organises them by funnel, and saves structured benchmarks to Supabase. This is the mandatory first step — all downstream skills depend on the data it produces.

---

## Overview

The skill runs three sequential phases:

| Phase | Name | Output table |
|-------|------|-------------|
| 1A | Ad Copy Winners | `ad_copy_winners` |
| 1B | Video Transcription | `ad_video_transcriptions` |
| 1C | Image Analysis | `ad_image_winners` |

Qualifying threshold: **spend ≥ $50 AND conversions ≥ 3**. Top 5 per asset type per funnel are saved.

---

## Phase 1A — Ad Copy Winners

Fetches all-time ad insights from the Meta Insights API and ranks ads by CPL (cost per lead) within each funnel.

### Key API call

```python
GET /{account_id}/insights
params = {
    "date_preset": "maximum",   # ← HARDCODED. NEVER change this.
    "level": "ad",
    "fields": "ad_id,ad_name,adset_name,campaign_name,spend,impressions,clicks,actions,cost_per_action_type",
    "limit": 500,
    "access_token": META_TOKEN,
}
```

> **`date_preset=maximum` is non-negotiable.** This pulls all-time data so CPL rankings are not distorted by short windows. Do not parameterise this.

### Qualifying action types

Only these action types count as conversions:

```python
LEAD_ACTION_TYPES = {
    "lead",
    "offsite_conversion.fb_pixel_lead",
    "omni_complete_registration",
}
```

See [`references/campaign-objectives.md`](../references/campaign-objectives.md) for how campaign objective affects which action type is populated.

### Supabase table written

**`ad_copy_winners`**

| Column | Description |
|--------|-------------|
| `winner_id` | `{client}_{funnel}_{type}_{ad_id}_{week}` |
| `account_id` | Meta account ID |
| `funnel_name` | Detected funnel key |
| `week_start` | ISO date string |
| `ad_id` | Meta ad ID |
| `ad_name` | Ad name from Meta |
| `asset_type` | `image` or `video` |
| `cpl` | Cost per lead |
| `spend` | Total spend |
| `conversions` | Qualifying conversion count |
| `headline` | Ad headline |
| `body_copy` | Ad body text |
| `rank` | 1–5 within funnel+type |

---

## Phase 1B — Video Transcription

Downloads each top video ad and transcribes the audio using OpenAI Whisper (CLI). Automatically tags hook, body, and CTA sections from the transcript.

**Whisper command used:**

```bash
whisper /tmp/vid_{ad_id}.mp4 \
  --model base \
  --language en \
  --output_format txt \
  --output_dir /tmp/
```

### Supabase table written

**`ad_video_transcriptions`**

| Column | Description |
|--------|-------------|
| `transcription_id` | `{client}_{funnel}_vid_{ad_id}_{week}` |
| `hook_text` | First 2 sentences |
| `body_text` | Between hook and CTA |
| `cta_text` | Last sentence if CTA keyword detected |
| `full_transcript` | Complete transcript |
| `hook_first_10` | First 10 words (niche signal check) |
| `word_count` | Total word count |

---

## Phase 1C — Image Analysis

Downloads top image ads and sends them to GPT-4o Vision for structured analysis. Extracts format type, visual elements, authenticity signals, and core message.

**9-point analysis extracted:**

1. FORMAT (reddit-screenshot / whiteboard / flat-lay / phone-screenshot / meme / typographic / other)
2. TEXT ON IMAGE
3. SETTING
4. PROPS
5. PERSON
6. COLOUR PALETTE
7. AUTHENTICITY SIGNALS
8. CORE VISUAL CLAIM
9. WHAT IS ABSENT

### Supabase table written

**`ad_image_winners`**

| Column | Description |
|--------|-------------|
| `image_winner_id` | `{client}_{funnel}_img_{ad_id}_{week}` |
| `image_format` | Format type string |
| `text_on_image` | All visible text |
| `setting` | Environment description |
| `props` | Physical objects visible |
| `authenticity_signals` | Organic/native signals |
| `core_visual_claim` | What the image communicates |
| `full_analysis` | Full JSON from GPT-4o |

---

## Quality Gates

After data is pulled, `run_quality_checks()` is executed automatically. It flags:

- **Learning phase ads** (`conversions_7d < 50`) — marked `is_learning = True`, excluded from CPL comparisons
- **3x kill flags** — any ad with CPL > 3× funnel median AND spend ≥ $100, flagged with `⚠️`
- **Underfunded ad sets** — where daily budget < (5 × CPA / 7)

Warnings are included in the markdown output. **No ads are paused or killed by this script.**

See [`references/quality-gates.md`](../references/quality-gates.md) for full thresholds.

---

## Compliance Checks

Before analysing any account, Skill 1 checks for Special Ad Categories:

```python
GET /act_{account_id}/campaigns?fields=special_ad_categories&limit=50
# If special_ad_categories != [] → flag "CREDIT CATEGORY ACTIVE"
```

See [`references/special-ad-categories.md`](../references/special-ad-categories.md) for affected accounts and restrictions.

---

## Campaign Objective Considerations

CPL comparisons are only valid within the same campaign objective type. Mixed-objective accounts trigger a warning.

See [`references/campaign-objectives.md`](../references/campaign-objectives.md) for:
- How each objective type (`OUTCOME_LEADS`, `OUTCOME_SALES`, etc.) affects action type counting
- ABO vs CBO behaviour
- Advantage+ Shopping Campaign (ASC) considerations

---

## CLI Usage

```bash
python3 skill1_winner_extraction.py --account profitable_tradie --week 2026-03-10
python3 skill1_winner_extraction.py --account all --week 2026-03-10
```

---

## Validation Loop

1. Run skill → check Supabase tables have rows for the expected funnels
2. Confirm `is_learning` flag is populated on all ads
3. Check warnings list — resolve any `⚠️ 3x KILL FLAG` entries with the media buyer
4. Confirm no `unknown` funnel appears in results (means a URL pattern is missing from `creative_config.py`)
5. Hand off to Skill 2 (`writing-ad-copy`)

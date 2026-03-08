# Creative Intelligence Pipeline — Meta Ads

A fully automated weekly pipeline that extracts top-performing Meta ad creative, generates new copy, image prompts, and video scripts grounded in all-time performance data, and delivers a complete Creative Brief (markdown + PDF) every Monday at 4am AEDT.

---

## What This Pipeline Does

1. **Pulls all-time top ads** from Meta Insights API (ranked by CPL, per funnel)
2. **Transcribes top video ads** using OpenAI Whisper (hook / body / CTA tagging)
3. **Analyses top image ads** using GPT-4o Vision (format, props, authenticity signals)
4. **Generates 20 new copy variants** per funnel — 2 concepts × 2 bodies × 5 hooks
5. **Generates 20 image prompts** matched to each copy variant
6. **Generates 10 video scripts** with validated hook staging directions
7. **Delivers a master Creative Brief** as both a markdown file and a PDF

All data flows through Supabase. Each skill is independently runnable.

---

## The Continuer / Explorer Framework

Every batch of hooks is split into two strategy types:

| Type | Hooks | Strategy |
|------|-------|----------|
| **Continuer** | H1, H2 | Almost identical to the proven winner hook. Retains exact numbers and phrasing. This is your **floor** — guaranteed to perform at or near winner level. |
| **Explorer** | H3, H4, H5 | Same emotional foundation as the winner, but from a new angle, entry point, or situation. These are hunting the **next winner**. |

**Why this split matters:** Continuers give you a safe baseline on Day 1. Explorers give you upside. Without Continuers you risk a cold start. Without Explorers you never discover a better hook.

---

## Pipeline Architecture

```
Skill 1 — extracting-ad-winners
  └─ Reads:  Meta Insights API
  └─ Writes: ad_copy_winners, ad_video_transcriptions, ad_image_winners

Skill 2 — writing-ad-copy
  └─ Reads:  ad_copy_winners, ad_video_transcriptions
  └─ Writes: ad_concepts (20 variants per funnel)

Skill 3 — writing-ad-images
  └─ Reads:  ad_concepts, ad_image_winners
  └─ Writes: ad_images (20 prompts per funnel)

Skill 4 — writing-video-scripts
  └─ Reads:  ad_concepts, ad_video_transcriptions
  └─ Writes: ad_video_scripts (10 scripts per funnel)

creative_pipeline.py (Orchestrator)
  └─ Runs Skills 1–4 in sequence
  └─ Builds master Creative Brief (markdown + PDF)
```

---

## Accounts

| Account | Meta Account ID | Funnels | Special Category |
|---------|----------------|---------|-----------------|
| Profitable Tradie | `act_559512967808213` | `labour_calc`, `ai_assistant`, `sys_blueprint`, `pricing_calc` | None |
| Fitribe | `act_947697689468163` | (TBC) | None |
| Strategic Mortgage Brokers | `act_2554789344674358` | (TBC) | Credit |
| USCCA | `act_343053550` | (TBC) | None |
| Dashdot | `act_229691921275637` | (TBC) | Credit (Financial Products) |
| Humphris Health | `act_323920064962831` | (TBC) | None |

> Accounts marked **Credit** have Special Ad Category restrictions. See [`references/special-ad-categories.md`](references/special-ad-categories.md).

---

## Weekly Schedule

Runs every **Monday at 4:00am AEDT** via cron:

```cron
0 17 * * 0  cd /path/to/scripts && python3 creative_pipeline.py --account all --week $(date +%Y-%m-%d)
```

> 4:00am AEDT = 17:00 UTC Sunday (AEDT = UTC+11 during daylight saving, UTC+10 otherwise)

---

## Output Format

### Markdown Brief
- Location: `{report_dir}/creative_brief_{funnel}_{week_start}.md`
- Contains: all 10 variants per funnel, each with copy, image prompts, and video script
- Organised by: Concept → Body → Hook variant

### PDF Brief
- Location: `{report_dir}/creative_brief_{funnel}_{week_start}.pdf`
- Format: A4, one section per variant
- Includes: clickable links to image URLs and source video ads
- Footer: "Confidential — Valher Media"

---

## Setup Instructions

### 1. Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
cp .env.example .env
```

Required variables:

```
META_ACCESS_TOKEN=your_meta_token
OPENAI_API_KEY=your_openai_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
```

### 2. Database Setup

Run the SQL setup script in Supabase (SQL Editor or CLI):

```bash
# Via Supabase CLI
supabase db push --file create_creative_tables.sql

# Or paste contents into Supabase SQL Editor
cat create_creative_tables.sql
```

Tables created:
- `ad_copy_winners`
- `ad_video_transcriptions`
- `ad_image_winners`
- `ad_concepts`
- `ad_images`
- `ad_video_scripts`

### 3. Python Dependencies

```bash
pip install requests openai supabase openai-whisper fpdf2
```

> Whisper also requires `ffmpeg`: `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux)

---

## Running the Pipeline

### Full pipeline (all accounts)
```bash
python3 creative_pipeline.py --account all --week 2026-03-10
```

### Single account
```bash
python3 creative_pipeline.py --account profitable_tradie --week 2026-03-10
```

### Individual skills
```bash
python3 skill1_winner_extraction.py --account profitable_tradie --week 2026-03-10
python3 skill2_ad_copy_writer.py --account profitable_tradie --funnel labour_calc --week 2026-03-10
python3 skill3_ad_image_writer.py --account profitable_tradie --funnel labour_calc --week 2026-03-10
python3 skill4_ad_video_writer.py --account profitable_tradie --funnel labour_calc --week 2026-03-10
```

---

## Campaign Objective Considerations

Different Meta campaign objectives populate different action types and have different CPL comparison validity rules. See [`references/campaign-objectives.md`](references/campaign-objectives.md) for:

- How `OUTCOME_LEADS`, `OUTCOME_SALES`, and other objectives affect action type counting
- ABO vs CBO behaviour and when to switch
- Advantage+ Shopping Campaign (ASC) analysis rules
- Learning phase detection and protection rules
- Mixed-objective warning logic

---

## Reference Files

| File | Purpose |
|------|---------|
| [`references/campaign-objectives.md`](references/campaign-objectives.md) | Meta objective types and their effect on this pipeline |
| [`references/special-ad-categories.md`](references/special-ad-categories.md) | Credit, Housing, Employment SAC restrictions |
| [`references/quality-gates.md`](references/quality-gates.md) | Kill rules, budget sufficiency, comparison validity |
| [`references/copy-rules.md`](references/copy-rules.md) | Full hook and body copy generation rules |
| [`references/image-formats.md`](references/image-formats.md) | All 7 proven image formats with performance data |
| [`references/staging-guide.md`](references/staging-guide.md) | Video hook staging locations, props, blocked actions |

---

## Skill Documentation

| File | Skill |
|------|-------|
| [`skills/skill1-winner-extraction.md`](skills/skill1-winner-extraction.md) | extracting-ad-winners |
| [`skills/skill2-ad-copy-writer.md`](skills/skill2-ad-copy-writer.md) | writing-ad-copy |
| [`skills/skill3-ad-image-writer.md`](skills/skill3-ad-image-writer.md) | writing-ad-images |
| [`skills/skill4-ad-video-writer.md`](skills/skill4-ad-video-writer.md) | writing-video-scripts |

---

## Confidential

This pipeline and its outputs are confidential to Valher Media and its clients. Do not share Creative Briefs externally without client approval.

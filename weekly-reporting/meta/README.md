# Meta Ads — Creative Intelligence Pipeline

Weekly automation that extracts winning ad creative, generates new copy, image briefs, and video scripts — all matched by concept ID so nothing gets mismatched when uploading to Meta.

## How It Works

| Skill | File | Does |
|---|---|---|
| 1 — Winner Extraction | `skill1_winner_extraction.py` | Pulls all-time top ads from Meta API. Transcribes video ads with Whisper. Analyses image ads with GPT-4o Vision. Saves to Supabase. |
| 2 — Ad Copy Writer | `skill2_ad_copy_writer.py` | Generates 2 concepts × 2 body copies × 5 hooks (Continuers + Explorers). |
| 3 — Ad Image Writer | `skill3_ad_image_writer.py` | Generates 20 × 500-word JSON image prompts, each matched to a specific hook. |
| 4 — Ad Video Writer | `skill4_ad_video_writer.py` | Generates full video scripts with Location + Prop + Action hook staging. |

## Run the Full Pipeline

```bash
python3 creative_pipeline.py --account profitable_tradie --week 2026-03-10
```

## Run Individual Skills

```bash
python3 skill1_winner_extraction.py --account profitable_tradie --week 2026-03-10
python3 skill2_ad_copy_writer.py --account profitable_tradie --funnel labour_calc --week 2026-03-10
python3 skill3_ad_image_writer.py --account profitable_tradie --funnel labour_calc --week 2026-03-10
python3 skill4_ad_video_writer.py --account profitable_tradie --funnel labour_calc --week 2026-03-10
```

## Setup

1. Run the SQL in `create_creative_tables.sql` via the Supabase SQL editor
2. Install dependencies: `pip3 install openai supabase requests openai-whisper`
3. Credentials are in `creative_config.py`

## Output

Each skill writes to Supabase and generates a markdown brief. The pipeline combines all 4 into one master `creative_brief_{funnel}_{week}.md` per funnel — organised by concept, with copy + images + video all in one place.

## Continuer / Explorer Framework

Every batch of 5 hooks per body copy is split:
- **H1, H2 = Continuers** — almost identical to proven winners. Your floor. High probability of success.
- **H3, H4, H5 = Explorers** — same emotional foundation, new angle. Hunting the next winner.

Never launch only untested creative.

# SKILL 1: Ad Winner Extraction
**Version:** 2.0 | **Part of:** Creative Intelligence Suite (Skill 1 of 4)

---

## PURPOSE

Pure data extraction. No writing, no generation. Pull everything that has worked — all time — from the Meta ad account and store it in Supabase so Skills 2, 3, and 4 can build from real proven creative.

Three extraction types run in sequence:
- **1A — Ad Copy Winners:** Written captions from top qualifying ads
- **1B — Video Transcriptions:** Whisper transcripts of top video ads
- **1C — Image Analysis:** Visual breakdown of top image ads

**Run order:** This skill runs FIRST. Skills 2, 3, and 4 all depend on its output.
Nothing in Skills 2-4 touches the Meta API. Everything they need comes from this skill.

---

## WHEN TO USE

- Runs every Monday at 4am AEDT as first step of the Creative Intelligence pipeline
- Can be re-run on demand for a specific account/funnel without affecting downstream skills
- Re-running overwrites Supabase data for that funnel/week (upsert)

---

## INPUTS / CONFIGURATION

```python
CONFIG = {
    "account_id": "act_559512967808213",
    "client_id": "c6065265-f986-47e4-b1b2-acd05afc61f0",
    "date_preset": "maximum",       # ALL TIME — mandatory, never change
    "min_spend_usd": 50,            # minimum spend to qualify
    "min_conversions": 3,           # minimum leads/conversions to qualify
    "top_n": 5,                     # top N ads per funnel per type
    "image_download_dir": "/Users/atlas/.openclaw/workspace/",
    "video_tmp_dir": "/tmp/",
    "week_start": "2026-03-10",     # ISO date of the Monday being run
    "funnels": {
        # Auto-detected via URL deduplication, or manually seeded:
        "labour_calc": {
            "base_url": "profitabletradie.com/labour",
            "offer_name": "Real Cost of Labour Calculator",
            "audience": "Australian trades business owners",
        }
        # Add per account
    }
}
```

---

## STEP 1A — AD COPY WINNER EXTRACTION

### Pull all-time ad insights

```python
GET https://graph.facebook.com/v21.0/act_{account_id}/insights

params = {
    "date_preset": "maximum",       # ALL TIME
    "level": "ad",
    "fields": "ad_id,ad_name,adset_name,campaign_name,spend,impressions,clicks,actions,cost_per_action_type",
    "limit": 500,
    "access_token": META_TOKEN
}
```

### Pull creative for each qualifying ad

```python
GET https://graph.facebook.com/v21.0/{ad_id}

params = {
    "fields": "creative{body,title,object_story_spec,asset_feed_spec,video_id,effective_object_story_id}",
    "access_token": META_TOKEN
}
```

### Filter criteria
- `spend >= CONFIG["min_spend_usd"]`
- `conversions >= CONFIG["min_conversions"]`
- Has a retrievable `creative.body` (skip if empty)

### Funnel detection (URL deduplication)

```python
from urllib.parse import urlparse

def get_funnel_from_url(url: str) -> str:
    """Strip all params, identify funnel from base URL slug."""
    parsed = urlparse(url)
    base = f"{parsed.netloc}{parsed.path}".rstrip("/").lower()
    # Match against CONFIG["funnels"] base_url keys
    for slug, config in CONFIG["funnels"].items():
        if config["base_url"] in base:
            return slug
    return base  # Use raw base URL as funnel key if not in config

def get_asset_type(creative: dict) -> str:
    if creative.get("video_id"):
        return "video"
    if creative.get("asset_feed_spec", {}).get("videos"):
        return "video"
    return "image"
```

### Take top N per funnel by CPL ascending

Per funnel, keep separate lists:
- `image_copy_winners` — top N image ads by CPL (written caption)
- `video_copy_winners` — top N video ads by CPL (caption only — transcription done in 1B)

### Save to Supabase

```sql
CREATE TABLE ad_copy_winners (
    winner_id       VARCHAR(64) PRIMARY KEY,
    -- e.g. "PT_LABOUR_IMG_ad123_2026W10"
    account_id      VARCHAR(32) NOT NULL,
    funnel_name     VARCHAR(128),
    week_start      DATE NOT NULL,
    ad_id           VARCHAR(32) NOT NULL,
    ad_name         TEXT,
    asset_type      VARCHAR(8),         -- 'image' or 'video'
    cpl             NUMERIC(10,2),
    spend           NUMERIC(10,2),
    conversions     INTEGER,
    headline        TEXT,               -- creative.title
    body_copy       TEXT,               -- creative.body (caption text)
    rank            SMALLINT,           -- 1 = best CPL
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

## STEP 1B — VIDEO TRANSCRIPTION

For each qualifying video ad (top N per funnel by CPL):

### Get video source URL

```python
GET https://graph.facebook.com/v21.0/{video_id}

params = {
    "fields": "source,description,length",
    "access_token": META_TOKEN
}
# "source" = downloadable video URL (expires — download immediately)
```

### Download video

```python
import requests, os

def download_video(url: str, ad_id: str, tmp_dir: str) -> str:
    out = os.path.join(tmp_dir, f"vid_{ad_id}.mp4")
    r = requests.get(url, timeout=60, stream=True)
    r.raise_for_status()
    with open(out, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
    return out
```

### Transcribe with Whisper

```bash
pip install openai-whisper  # if not installed
whisper /tmp/vid_{ad_id}.mp4 --model base --language en --output_format txt --output_dir /tmp/
```

```python
import subprocess

def transcribe(video_path: str) -> str:
    txt_path = video_path.replace(".mp4", ".txt")
    subprocess.run([
        "whisper", video_path,
        "--model", "base",
        "--language", "en",
        "--output_format", "txt",
        "--output_dir", "/tmp/"
    ], check=True)
    with open(txt_path) as f:
        return f.read().strip()
```

### Tag transcript sections

```python
def tag_transcript(transcript: str) -> dict:
    """
    Split transcript into hook / body / cta.
    Hook = first 1-2 sentences (approx first 40 words).
    CTA = last sentence(s) containing action words.
    Body = everything between.
    """
    sentences = transcript.split(". ")
    hook = ". ".join(sentences[:2])
    cta_keywords = ["link", "below", "free", "grab", "click", "download", "calculator"]
    cta = next((s for s in reversed(sentences) if any(k in s.lower() for k in cta_keywords)), sentences[-1])
    body = transcript[len(hook):transcript.rfind(cta)].strip()
    first_10 = " ".join(transcript.split()[:10])
    return {
        "hook_text": hook,
        "body_text": body,
        "cta_text": cta,
        "full_transcript": transcript,
        "hook_first_10": first_10,
        "word_count": len(transcript.split())
    }
```

### Save to Supabase

```sql
CREATE TABLE ad_video_transcriptions (
    transcription_id    VARCHAR(64) PRIMARY KEY,
    -- e.g. "PT_LABOUR_VID_ad123_2026W10"
    ad_id               VARCHAR(32) NOT NULL,
    account_id          VARCHAR(32) NOT NULL,
    funnel_name         VARCHAR(128),
    week_start          DATE NOT NULL,
    cpl                 NUMERIC(10,2),
    spend               NUMERIC(10,2),
    conversions         INTEGER,
    rank                SMALLINT,
    hook_text           TEXT,
    body_text           TEXT,
    cta_text            TEXT,
    full_transcript     TEXT NOT NULL,
    hook_first_10       VARCHAR(256),
    word_count          INTEGER,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
```

---

## STEP 1C — IMAGE ANALYSIS

For each qualifying image ad (top N per funnel by CPL):

### Download image

```python
def download_image(ad: dict, funnel_slug: str, rank: int, save_dir: str) -> str:
    img_url = (ad.get("creative", {}).get("image_url")
               or ad.get("creative", {}).get("thumbnail_url"))
    if not img_url:
        return None
    ext = "jpg" if "jpg" in img_url.lower() else "png"
    filename = f"{funnel_slug}_{rank}.{ext}"
    path = os.path.join(save_dir, filename)
    r = requests.get(img_url, timeout=30)
    if len(r.content) < 20_000:  # skip tiny/corrupt files
        return None
    with open(path, "wb") as f:
        f.write(r.content)
    return path
```

### Analyse with vision model

For each downloaded image, extract:

```
1. FORMAT: overall layout type
   (reddit-screenshot / whiteboard / flat-lay / phone-screenshot /
    meme / typographic / split-panel / site-candid / other)

2. TEXT ON IMAGE: exact wording of every piece of text visible
   (whiteboard writing, phone screen content, printed document text,
    handwriting, overlaid captions — word for word)

3. SETTING: exact environment
   (job site / ute interior / workshop / home office / outdoor / kitchen / etc.)

4. PROPS: every physical object visible
   (tools, devices, documents, clothing items, food/drink containers)

5. PERSON: if visible
   (hands only / forearms / full body / face shown yes/no,
    clothing description, action being performed)

6. COLOUR PALETTE: dominant colours (hex where identifiable)

7. AUTHENTICITY SIGNALS: what makes it look organic/native
   (worn tools, real UI, handwriting, site context, imperfect composition)

8. CORE VISUAL CLAIM: what does this image communicate before any text is read?

9. WHAT IS ABSENT: no branding / no stock-photo feel / no studio setup
```

### Save to Supabase

```sql
CREATE TABLE ad_image_winners (
    image_winner_id     VARCHAR(64) PRIMARY KEY,
    -- e.g. "PT_LABOUR_IMG_ad123_2026W10"
    ad_id               VARCHAR(32) NOT NULL,
    account_id          VARCHAR(32) NOT NULL,
    funnel_name         VARCHAR(128),
    week_start          DATE NOT NULL,
    cpl                 NUMERIC(10,2),
    spend               NUMERIC(10,2),
    conversions         INTEGER,
    rank                SMALLINT,
    local_file_path     TEXT,
    image_format        VARCHAR(32),        -- reddit-screenshot / whiteboard / etc.
    text_on_image       TEXT,               -- all visible text, verbatim
    setting             TEXT,
    props               TEXT,
    person_description  TEXT,
    colour_palette      TEXT,
    authenticity_signals TEXT,
    core_visual_claim   TEXT,
    full_analysis       TEXT,               -- complete analysis JSON
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
```

---

## OUTPUT (console + log file)

```
WINNER EXTRACTION COMPLETE — PT / labour_calc / Week 2026W10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1A — Ad Copy Winners:      5 image ads, 5 video ads saved
1B — Video Transcriptions: 4/5 transcribed (1 video URL 403 — skipped)
1C — Image Analysis:       5/5 downloaded and analysed

Top performers saved:
  Image #1: IMG-690 | CPL $1.80 | 177 leads | Format: reddit-screenshot
  Image #2: IMG-141 | CPL $2.51 | 123 leads | Format: monitor-with-annotation
  Video #1: VID-184 | CPL $1.90 | 87 leads  | Hook: "I worked 237 days straight..."
  Video #2: VID-205 | CPL $2.10 | 64 leads  | Hook: "My apprentice asked me..."

Supabase tables updated:
  ad_copy_winners         → 10 rows
  ad_video_transcriptions → 4 rows
  ad_image_winners        → 5 rows

Ready for Skill 2.
```

---

## EDGE CASES

| Situation | Handling |
|-----------|----------|
| Video source URL returns 403/404 | Skip; log; continue |
| Video download times out | Retry once; skip if still fails |
| Whisper not installed | Error: `pip install openai-whisper`; do not skip silently |
| Image file < 20KB | Skip (corrupt or tracking pixel) |
| Fewer than 3 qualifying ads | Use all; note "Limited data — N ads qualified" |
| No body copy in creative | Skip for 1A; flag in log |
| No video ads qualify for this funnel | Note in log; 1B skipped; Skills 2 and 4 still run (image-only) |
| Meta API rate limit | Backoff 60s, retry twice, then fail with log |

---

## IMPROVEMENT BACKLOG

- [ ] Whisper model upgrade: `medium` or `large-v3` for noisy job-site audio
- [ ] Timestamp tagging: store Whisper timestamp output to identify exact hook duration
- [ ] Speaker diarisation: for multi-speaker interview/testimonial formats
- [ ] Image duplicate detection: hash check before download — skip exact duplicates
- [ ] Auto-classify image format using vision model output → store as structured tag

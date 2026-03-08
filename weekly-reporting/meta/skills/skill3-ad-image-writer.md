---
name: writing-ad-images
description: Reads top image ad analyses and copy concepts from Supabase. Generates 20 × 500-word JSON image prompts — 2 per ad variant (10 variants = 2 concepts × 2 bodies × 5 hooks). Each prompt is matched to its specific hook so copy and image can never mismatch. Option A uses the winning format; Option B uses a different format. Use after writing-ad-copy.
---

# Skill 3 — Writing Ad Images

Generates detailed image prompts for every ad variant produced by Skill 2. Each prompt is a ~500-word JSON object describing the exact visual execution — format, setting, props, text overlay, and authenticity signals — matched precisely to its hook's emotional entry point.

---

## Prerequisites

Run `writing-ad-copy` (Skill 2) first. This skill reads from:
- `ad_concepts` — the 20 copy variants (concept × body × hook)
- `ad_image_winners` — GPT-4o Vision analyses of top-performing image ads

---

## The Maths: Why 20 Prompts

```
2 concepts
  × 2 body variants (A, B)
    × 5 hooks (H1–H5)
      = 10 ad variants

Each variant gets 2 image options (A and B):
  Option A → uses the winning image format
  Option B → uses a different proven format (pattern interrupt)

10 variants × 2 images = 20 image prompts
```

> The 20-prompt output feeds directly into Skill 4 (video scripts). Images and scripts cover the same 10 variants — together they complete the full Creative Brief.

---

## Hook Alignment Rule

**Each image prompt is locked to its specific hook.** The visual must reinforce the same emotional trigger as the hook text.

- The first 10 words of the hook define the visual situation
- The image prompt references those exact words to ensure alignment
- You cannot swap an image from H1 onto H3 — the emotional entry points are different

This is enforced in the prompt construction:
```python
for hook in concept.hooks:
    prompt = build_image_prompt(
        hook=hook.text,          # hook locked in
        format_a=winner_format,  # Format A = winning format
        format_b=alternate_format,
        analysis=image_winner_analysis,
    )
```

---

## Image Option A vs Option B

| Option | Format Used | Logic |
|--------|-------------|-------|
| A | Winner format (from `ad_image_winners.image_format`) | Replicates the format that produced the lowest CPL |
| B | Next best or deliberately different format | Pattern interrupt — same hook, different visual execution |

See [`references/image-formats.md`](../references/image-formats.md) for all 7 proven formats and their performance data.

---

## JSON Prompt Structure

Each prompt is a JSON object (~500 words) with these fields:

```json
{
  "format": "reddit-screenshot",
  "hook_reference": "I worked 237 days straight before I figured this out",
  "visual_concept": "Authentic Reddit post screenshot showing a tradie's confession...",
  "setting": {
    "environment": "Reddit dark mode interface",
    "subreddit": "r/AussieTrades",
    "post_title": "Finally figured out why I was always broke despite being fully booked",
    "upvote_count": "847",
    "comments_visible": true
  },
  "username": "concreter_QL_travis",
  "text_on_image": "Full post body text here...",
  "authenticity_signals": [
    "Low karma account (3 years old)",
    "Comment count visible",
    "Award icon present"
  ],
  "what_is_absent": ["brand logos", "stock photography", "studio lighting"],
  "colour_palette": "Reddit dark mode — near-black background, orange accent",
  "technical_specs": {
    "aspect_ratio": "1:1 or 4:5",
    "resolution": "1080x1080 or 1080x1350",
    "safe_zone": "No important content in outer 10%"
  },
  "ai_generation_notes": "Generate as photorealistic screenshot. Font must match Reddit's default (IBM Plex Sans)."
}
```

---

## Supabase Table Written

**`ad_images`**

| Column | Description |
|--------|-------------|
| `image_id` | `{variant_id}_IMG_{A|B}` |
| `account_id` | Meta account ID |
| `funnel_name` | Funnel key |
| `week_start` | ISO date string |
| `variant_id` | Matches `ad_concepts` hook variant |
| `image_option` | `A` or `B` |
| `image_format` | Format type string |
| `json_prompt` | Full ~500-word JSON prompt |
| `image_url` | Populated later (if image is generated externally) |

---

## CLI Usage

```bash
python3 skill3_ad_image_writer.py --account profitable_tradie --funnel labour_calc --week 2026-03-10
```

---

## Validation Loop

1. Confirm `ad_images` table has exactly 20 rows per funnel (10 variants × 2 options)
2. Spot-check 3 prompts — confirm `hook_reference` field matches the actual hook text in `ad_concepts`
3. Confirm Image A and Image B use different `image_format` values for the same variant
4. Check `what_is_absent` list includes "brand logos" and "stock photography" for organic-format ads
5. Hand off JSON prompts to image generation (DALL-E 3, Midjourney, or human designer)

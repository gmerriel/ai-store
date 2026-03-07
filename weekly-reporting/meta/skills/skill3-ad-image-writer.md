# SKILL 3: Ad Image Writer
**Version:** 2.0 | **Part of:** Creative Intelligence Suite (Skill 3 of 4)

---

## PURPOSE

Read winning image ad analysis from Skill 1 (Supabase) and concept_ids from Skill 2. Generate 20 × 500+ word JSON image prompts — 2 per ad variant, each precisely matched to its paired hook so copy and image can never be mismatched.

Does not touch the Meta API. Reads only from Supabase.

**Run order:** Runs third. Requires Skills 1 and 2 to have completed.

---

## THE MATHS OF 20

```
2 concepts (C1, C2)
× 2 body copies per concept (A, B)
× 5 hooks per body
= 10 unique ad variants

× 2 image options per variant (primary + secondary format)
= 20 image prompts
```

Each of the 10 ad variants gets:
- **Image Option A** — built from the winning visual format (benchmark)
- **Image Option B** — a different format exploring the same hook, 5-10% variation in concept

---

## WHEN TO USE

- Runs every Monday at 4am AEDT, after Skill 2 completes
- Can be run on-demand if Skill 2 data exists in Supabase

---

## STEP 1 — READ FROM SUPABASE

```python
# Read image analysis from Skill 1
image_winners = supabase.table("ad_image_winners") \
    .select("*") \
    .eq("account_id", account_id) \
    .eq("funnel_name", funnel_name) \
    .eq("week_start", week_start) \
    .order("cpl", desc=False) \
    .execute().data

# Read concept_ids and hooks from Skill 2
concepts = supabase.table("ad_concepts") \
    .select("*") \
    .eq("account_id", account_id) \
    .eq("funnel_name", funnel_name) \
    .eq("week_start", week_start) \
    .execute().data

if not image_winners:
    raise RuntimeError("No image winner data. Run ad-winner-extraction (Skill 1) first.")
if not concepts:
    raise RuntimeError("No concept data. Run ad-copy-writer (Skill 2) first.")
```

---

## STEP 2 — IDENTIFY WINNING VISUAL PATTERNS

From `image_winners`, extract:

```
WINNING FORMAT: what layout type dominated the top 2-3 by CPL?
(reddit-screenshot / whiteboard / flat-lay / phone-screenshot / etc.)

AUTHENTICITY SIGNALS: what made the top image look native/organic?
(worn tools, real UI elements, handwriting, imperfect composition, site context)

TEXT ON IMAGE: what did the text in the top image say?
(this becomes the model for what text appears in new prompts)

WHAT IS ABSENT in top performers:
(studio backgrounds, visible branding, stock-photo props, clean/staged scenes)

FORMAT PRIORITY ORDER:
1. [winning format] — benchmark for Image Option A
2. [second format] — candidate for Image Option B
```

---

## STEP 3 — GENERATE 20 JSON IMAGE PROMPTS

For each of the 10 ad variants (C1_A_H1 through C2_B_H5), write 2 JSON prompts.

### Hook alignment rule
Each prompt must reflect its paired hook. The image should visualise the specific claim, scenario, or emotional moment in the hook text. When text appears in the image (e.g. a Reddit post headline, a whiteboard message, a sticky note), it must echo the hook's specific language — not a generic message about the offer.

```
Hook: "I worked 237 days straight. My wife went to bed alone most nights."
→ Image text (if Reddit format): "237 days straight. Never took a day off. Lost money the whole time."
→ NOT: "Are you undercharging for your labour?"

Hook: "My apprentice asked why he's charged out at $120 but paid $34."
→ Image text (if whiteboard): "Why am I charged at $120 but paid $34? (The real answer)"
→ NOT: "Calculate your real labour cost"
```

### JSON prompt structure (every field required, 500+ words total)

```json
{
  "image_id": "PT_LABOUR_C1_A_H1_IMG_A",
  "concept_id": "PT_LABOUR_C1_2026W10",
  "body_ref": "A",
  "hook_index": 1,
  "hook_type": "continuer",
  "image_option": "A",
  "paired_hook_text": "[exact hook text from Skill 2]",

  "image_generation_prompt": {

    "format": "square 1080×1080px Facebook/Instagram ad",

    "layout": "[overall composition — e.g. 'full-bleed Reddit screenshot displayed on a phone held in a tradie's hand, phone taking 80% of frame, rough concrete background barely visible']",

    "primary_subject": {
      "type": "[reddit-screenshot / whiteboard / flat-lay / phone-screenshot / etc.]",
      "description": "[precise multi-sentence description of the hero element — what it is, what it shows, exact text visible on it, its condition, its position in frame]",
      "text_content": {
        "element_1": {
          "exact_text": "[word for word — do not paraphrase]",
          "style": "[bold/regular/handwritten/marker/digital]",
          "colour": "[hex or precise description]",
          "position": "[where in the element — e.g. 'post title, top of Reddit card']"
        }
      }
    },

    "setting": {
      "location": "[exact environment — e.g. 'residential job site, timber frame visible, morning light']",
      "surface": "[what objects rest on — e.g. 'aluminium ute tray, slightly dusty']",
      "background": "[what is visible behind/around the subject — describe depth of field]",
      "lighting": "[type / direction / colour temperature — e.g. 'harsh midday outdoor sun, hard shadows, warm 5500K']",
      "time_of_day": "[morning / midday / evening / night]"
    },

    "props": [
      {
        "item": "[specific object — e.g. 'yellow Stanley tape measure']",
        "brand_model": "[if relevant — e.g. 'Stanley FatMax 8m']",
        "condition": "[new / worn / dirty / well-used]",
        "position": "[where in frame]",
        "detail": "[any markings, colour, distinguishing features]"
      }
    ],

    "person": {
      "present": true,
      "visible_parts": "[hands only / forearms / torso / full body — NEVER show face unless specified]",
      "clothing": "[specific — e.g. 'navy blue Tradie brand polo, slightly dusty, sleeves rolled to elbow']",
      "hands": "[callused / work-worn / wedding ring / glove marks from tanned line]",
      "action": "[what they are doing — must not block speech if this is a video staging]"
    },

    "colour_palette": [
      "[primary colour — hex]",
      "[secondary colour — hex]",
      "[accent / text colour — hex]",
      "[background tone]"
    ],

    "mood": "[the emotional feeling the image creates before any text is read — 1-2 sentences]",

    "authenticity_signals": [
      "[specific detail that makes it look organic — e.g. 'image is slightly off-centre, as if photographed hastily']",
      "[another signal — e.g. 'tool has visible use marks and a small dent']",
      "[another — e.g. 'phone screen has a tiny crack in the corner bezel']"
    ],

    "hook_alignment": "[1-2 sentences explaining exactly how this image reflects the specific paired hook — e.g. 'The Reddit post headline mirrors the hook's 237-day claim word-for-word, so the hook and image tell the same story simultaneously']",

    "avoid": [
      "studio lighting or backgrounds",
      "visible brand logos or marketing materials",
      "stock-photo composition (perfectly centred, everything pristine)",
      "any object that doesn't belong in a working tradie's environment",
      "[any other specific thing to avoid for this funnel/concept]"
    ],

    "ai_generation_notes": {
      "preferred_model": "[Gemini — for photorealistic / DALL-E 3 — for graphic or typographic]",
      "critical_details": "[the 2-3 things the AI must get exactly right or the image fails]",
      "style_reference": "[describe the photography/design style — e.g. 'candid documentary photography, like a journalist photographed this without setup']"
    }
  }
}
```

### Image Option B (5-10% variation)

Option B uses a different visual format from Option A but tells the same hook story. The JSON is rewritten for the new format — not copy-pasted with minor tweaks.

```
If Option A = Reddit screenshot
→ Option B = Google Sheets calculator on monitor with annotation
  (both tell the "$94 real cost vs $68 charged" story — different visual vehicle)

If Option A = whiteboard in workshop
→ Option B = handwritten note flat-lay on workbench
  (both surface the same message — different medium)
```

The hook_alignment field must still hold — Option B's image must still clearly reflect the paired hook.

---

## STEP 4 — SAVE TO SUPABASE

```sql
CREATE TABLE ad_images (
    image_id          VARCHAR(64) PRIMARY KEY,
    -- e.g. "PT_LABOUR_C1_A_H1_IMG_A"
    concept_id        VARCHAR(64) NOT NULL REFERENCES ad_concepts(concept_id),
    body_ref          CHAR(1) NOT NULL,       -- 'A' or 'B'
    hook_index        SMALLINT NOT NULL,      -- 1 to 5
    hook_type         VARCHAR(16),            -- 'continuer' or 'explorer'
    image_option      CHAR(1) NOT NULL,       -- 'A' (primary) or 'B' (variant)
    paired_hook_text  TEXT,
    json_prompt       TEXT NOT NULL,          -- full 500+ word JSON prompt
    image_format      VARCHAR(32),            -- reddit-screenshot / whiteboard / etc.
    image_url         TEXT,                   -- NULL until generated in Phase 2
    model_used        VARCHAR(32),            -- 'gemini' or 'dall-e-3'
    created_at        TIMESTAMPTZ DEFAULT NOW()
);
```

---

## STEP 5 — OUTPUT FORMAT (markdown doc for team)

```markdown
# Image Brief — [FUNNEL] — Week of [DATE]

---

## WINNING VISUAL ANALYSIS

| Rank | Format | CPL | Core Visual Claim |
|------|--------|-----|-------------------|
| 1 | Reddit screenshot | $1.80 | "Real labour cost hidden from tradies" |
| 2 | Monitor + annotation | $2.51 | "The calculator showing the real number" |

**Priority format for Image A:** Reddit screenshot (best CPL — extend this)
**Priority format for Image B:** Monitor/spreadsheet (second best — proven format)
**What NOT to do:** [list anti-patterns from winner analysis]

---

## IMAGE BRIEFS

### PT_LABOUR_C1_A_H1_IMG_A — Continuer | Body A | Hook 1
**Paired hook:** "[hook text]"
**Format:** Reddit Post Screenshot

\```json
{ [500+ word JSON] }
\```

### PT_LABOUR_C1_A_H1_IMG_B — Continuer | Body A | Hook 1 (variant)
**Paired hook:** "[same hook]"
**Format:** Google Sheets on Monitor

\```json
{ [500+ word JSON] }
\```

[... all 20 briefs ...]

---
*image_ids saved to Supabase: ad_images*
```

---

## PHASE 2 — IMAGE GENERATION (future)

When activated, reads `ad_images` where `image_url IS NULL` and calls:
- `Gemini 2.0 Flash` image generation API → photorealistic formats
- `DALL-E 3` API → graphic / typographic formats

Saves generated image to `/Users/atlas/reports/{client_slug}/images/` and updates `image_url` in Supabase.

---

## EDGE CASES

| Situation | Handling |
|-----------|----------|
| No image winner data | Error: run Skill 1 first |
| No concept data | Error: run Skill 2 first |
| Fewer than 2 image formats identified from winners | Use 1 format for both A and B; note in output |
| Hook text not found in Supabase | Error: Skill 2 data incomplete |

---

## IMPROVEMENT BACKLOG

- [ ] Phase 2: wire Gemini + DALL-E APIs for auto-generation
- [ ] Validate Option A vs Option B are genuinely different formats (not trivial variations)
- [ ] Track which generated images get used → feed back into next week's format priority
- [ ] Score "organic feel" of prompts before saving (checklist: no studio / no branding / has authenticity signals)

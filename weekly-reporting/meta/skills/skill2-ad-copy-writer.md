---
name: writing-ad-copy
description: Reads all-time top ad copy and video transcriptions from Supabase and generates 2 new main body copies with 5 hooks each per funnel. Hooks split into Continuers (almost identical to proven winners — your floor) and Explorers (same foundation, new angle — hunting the next winner). Run after extracting-ad-winners. Saves concepts to Supabase.
---

# Skill 2 — Writing Ad Copy

Generates new ad copy grounded in all-time winner benchmarks pulled by Skill 1. Output is 2 concepts × 2 body variants × 5 hooks = **20 copy variants per funnel**. Each variant is saved as a structured row in Supabase for use by Skills 3 and 4.

---

## Prerequisites

Run `extracting-ad-winners` (Skill 1) first. This skill reads from:
- `ad_copy_winners` — written captions from top image and video ads
- `ad_video_transcriptions` — Whisper-transcribed video scripts (hook, body, CTA)

---

## The Continuer / Explorer Framework

Every batch of 5 hooks is split into two categories:

| Hook | Type | Strategy |
|------|------|----------|
| H1 | CONTINUER | Almost identical to the proven winner hook. Retain exact numbers and phrasing. This is your floor — it should perform at least as well. |
| H2 | CONTINUER | Slight variation of H1 — swap one element (different number, different timeframe, same emotional payload). |
| H3 | EXPLORER | Same emotional foundation as winner, but new entry point / new situation. Hunting the next winner. |
| H4 | EXPLORER | Different angle — different pain trigger, same niche signal. |
| H5 | EXPLORER | Furthest from winner — highest risk, highest potential upside. |

> **Why this structure?** Continuers guarantee near-winner performance on Day 1. Explorers discover the next winner. You always have a floor; you're always hunting the ceiling.

---

## Hook Rules

1. **First 10 words must signal the niche via action or pain — never by naming the audience.**
   - ✅ `"I worked 237 days straight"` (only a tradie owner does this)
   - ❌ `"Are you a trades business owner?"`
2. Continuers retain the **exact numbers** from the winning hook.
3. Explorers start from a new situation but carry the same emotional tension.
4. No corporate language in any hook or body.

See [`references/copy-rules.md`](../references/copy-rules.md) for full rules, niche signal examples, and forbidden words.

---

## Word Counts

| Section | Target |
|---------|--------|
| Hook | 35–55 words |
| Body | 150–200 words |

Word counts are validated in the GPT-4o response. If counts fall outside range, the model is asked to revise.

---

## GPT-4o Prompt Structure

```
SYSTEM: You are an expert direct-response copywriter for [niche].

INPUT:
- Top 5 ad copy winners (body + hook from Supabase)
- Top 5 video transcripts (hook + body + CTA from Supabase)
- Funnel context: [funnel name, destination URL, offer]

TASK:
Generate 2 body copies (Body A and Body B), each with 5 hooks.
Hooks 1-2 are CONTINUERS (near-identical to winner).
Hooks 3-5 are EXPLORERS (new angle, same niche signal).

RULES:
[see references/copy-rules.md]

OUTPUT FORMAT:
Return a JSON object with the following structure:
{
  "concept_name": "...",
  "body_a": "...",
  "body_b": "...",
  "hooks_a": [
    {"index": 1, "type": "continuer", "text": "...", "word_count": 0},
    ...
  ],
  "hooks_b": [...]
}
```

---

## Supabase Table Written

**`ad_concepts`**

| Column | Description |
|--------|-------------|
| `concept_id` | `{client}_{funnel}_C{num}_{week}` |
| `concept_num` | 1 or 2 |
| `concept_name` | Short descriptive name |
| `inspired_by` | Source ad ID or transcript ID |
| `headline` | Ad headline |
| `body_a` | First body copy variant |
| `body_b` | Second body copy variant |
| `hooks_a` | JSON array of 5 hooks for Body A |
| `hooks_b` | JSON array of 5 hooks for Body B |
| `week_start` | ISO date string |

---

## Output per Funnel

```
Concept 1
  Body A → H1 (CONTINUER), H2 (CONTINUER), H3 (EXPLORER), H4 (EXPLORER), H5 (EXPLORER)
  Body B → H1–H5 (same split)
Concept 2
  Body A → H1–H5
  Body B → H1–H5
```

Total: **20 copy variants per funnel** → feeds directly into Skill 3 (images) and Skill 4 (video scripts).

---

## CLI Usage

```bash
python3 skill2_ad_copy_writer.py --account profitable_tradie --funnel labour_calc --week 2026-03-10
```

---

## Validation Loop

1. Check `ad_concepts` table — confirm 2 concepts per funnel with 5 hooks each
2. Spot-check word counts: body should be 150–200, hooks 35–55
3. Check H1/H2 hooks are recognisably similar to the winning ad copy
4. Check H3–H5 hooks do not name the audience directly
5. Confirm CTA in body matches the winning CTA phrase
6. Hand off to Skill 3 (`writing-ad-images`) and Skill 4 (`writing-video-scripts`)

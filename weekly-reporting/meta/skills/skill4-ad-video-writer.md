---
name: writing-video-scripts
description: Reads copy concepts and video transcription benchmarks from Supabase. Generates complete video ad scripts for each hook variant: Location + Prop + Action staging directions for the hook only, then full teleprompter body + CTA formatted for speech. Validates that staging actions cannot block speech. Use after writing-ad-copy.
---

# Skill 4 — Writing Video Scripts

Generates complete video ad scripts for all 10 hook variants per funnel (2 concepts × 2 bodies × 5 hooks). Each script includes hook staging directions and a full teleprompter-ready body. Staging actions are validated to ensure they cannot physically block speech.

---

## Prerequisites

Run `writing-ad-copy` (Skill 2) first. This skill reads from:
- `ad_concepts` — hook text and body copy for each variant
- `ad_video_transcriptions` — benchmark video structures (hook timing, body pacing, CTA phrasing)

---

## Script Structure

Each video script has two distinct sections:

### Section 1: Hook Staging (visual directions only)

**Only the hook gets Location + Prop + Action staging.** The hook is the only part of the script where the performer is doing something in a specific place. This creates the authenticity signal.

```
HOOK STAGING
  Location : White ute cab, driver's seat, engine off, morning light
  Prop     : Clipboard with handwritten quote sheet on passenger seat
  Action   : Looking at clipboard, looks up to camera
  Energy   : Surprised/realising — like they just figured something out
```

**The action must not block speech.** Looking at a clipboard = fine. Drinking coffee = blocked. Hammering = too loud. See blocked actions list below.

### Section 2: Teleprompter Script

Everything after the hook is written as a clean teleprompter script — spoken directly to camera, no staging directions needed.

```
TELEPROMPTER
[HOOK — speak first]
I worked 237 days straight before I figured out why I was still broke.

[BODY — deliver to camera]
I was pricing every job the same way I always had. Just copying what I thought
the job was worth. Turns out I wasn't even covering my real cost of labour...

[CTA — exact phrase from winner]
Click the link below and grab the free Labour Rate Calculator.
```

---

## Blocked Actions

The following actions are flagged automatically and the script is rejected:

| Action | Reason |
|--------|--------|
| Drinking or eating | Mouth occupied — cannot speak |
| Operating power tools | Noise + safety |
| Driving | Safety + camera angle |
| On a phone call | Audience confused about who they're talking to |
| Hammering, sawing, drilling | Too loud, cuts speech |
| Carrying heavy load | Can't speak comfortably |

If a blocked action is detected in the draft, the model is prompted to revise with an alternative from the approved list.

---

## Validation Logic

```python
BLOCKED_ACTIONS = [
    "drinking", "eating", "driving", "phone call",
    "hammering", "sawing", "drilling", "carrying",
]

def validate_action(action: str) -> tuple[bool, str]:
    """Returns (is_valid, warning_message)"""
    for blocked in BLOCKED_ACTIONS:
        if blocked in action.lower():
            return False, f"Blocked action detected: '{blocked}' — performer cannot speak."
    return True, ""
```

Rows with `action_valid = False` are flagged in the master brief with `⚠️`.

---

## Full Script Format in Supabase

**`ad_video_scripts`**

| Column | Description |
|--------|-------------|
| `script_id` | `{variant_id}_VID` |
| `account_id` | Meta account ID |
| `funnel_name` | Funnel key |
| `week_start` | ISO date string |
| `variant_id` | Matches `ad_concepts` hook variant |
| `location` | Approved location (from staging guide) |
| `prop` | Approved prop (from staging guide) |
| `action` | What performer is doing during hook |
| `energy` | Tone/emotion for hook delivery |
| `full_script` | Complete teleprompter script |
| `estimated_seconds` | Word count ÷ 2.5 (approx speech rate) |
| `action_valid` | Boolean — False if blocked action detected |
| `action_warning` | Warning message if action_valid = False |

---

## Approved Locations and Props

See [`references/staging-guide.md`](../references/staging-guide.md) for:
- Full list of approved locations with best-use context
- Full list of approved props with usage rules
- Detailed guidance on combining location + prop for maximum authenticity

---

## CLI Usage

```bash
python3 skill4_ad_video_writer.py --account profitable_tradie --funnel labour_calc --week 2026-03-10
```

---

## Validation Loop

1. Check `ad_video_scripts` table has exactly 10 rows per funnel
2. Verify `action_valid = True` for all rows — resolve any ⚠️ flags before briefing talent
3. Check `estimated_seconds` — aim for 45–75s total (hook ~10s + body ~35–55s + CTA ~5s)
4. Confirm `full_script` starts with the exact hook text from `ad_concepts`
5. Confirm CTA phrase matches the winning CTA from `ad_video_transcriptions`
6. Scripts are production-ready — hand to talent briefing document

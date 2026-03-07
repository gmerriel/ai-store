# SKILL 4: Ad Video Script Writer
**Version:** 2.0 | **Part of:** Creative Intelligence Suite (Skill 4 of 4)

---

## PURPOSE

Read concepts from Skill 2 and video transcriptions from Skill 1. For each hook variant, produce a complete video ad script — a full teleprompter-ready document. The hook gets "Location + Prop + Action" staging directions to stop the scroll in the first 3 seconds. The body and CTA come directly from Skill 2's copy and are formatted for speech.

Does not touch the Meta API. Reads only from Supabase.

**Run order:** Runs fourth. Requires Skills 1 and 2 to have completed.

---

## THE HOOK IS THE ONLY THING WITH STAGING

Every hook gets:
- **LOCATION** — where is the person? (must feel immediately authentic to the niche)
- **PROP** — what are they holding or interacting with?
- **ACTION** — what are they doing as they begin to speak?

The body and CTA have no staging directions — they are spoken straight to camera after the hook scene is established.

**Why only the hook?**
The hook's job is to stop the scroll in the first 2-3 seconds — before the viewer has decided to keep watching. The visual context (where the person is, what they're doing) communicates the niche and credibility instantly, even to viewers watching without sound. Once the viewer is watching, the copy does the work.

---

## WHEN TO USE

- Runs every Monday at 4am AEDT, after Skills 1 and 2 complete
- Can be run on-demand if Skill 1 and 2 data exists in Supabase

---

## STEP 1 — READ FROM SUPABASE

```python
# Read video transcriptions (Skill 1 output — benchmarks)
transcriptions = supabase.table("ad_video_transcriptions") \
    .select("*") \
    .eq("account_id", account_id) \
    .eq("funnel_name", funnel_name) \
    .eq("week_start", week_start) \
    .order("cpl", desc=False) \
    .execute().data

# Read concepts and hooks (Skill 2 output)
concepts = supabase.table("ad_concepts") \
    .select("*") \
    .eq("account_id", account_id) \
    .eq("funnel_name", funnel_name) \
    .eq("week_start", week_start) \
    .execute().data

if not concepts:
    raise RuntimeError("No concept data. Run ad-copy-writer (Skill 2) first.")
# transcriptions can be empty (image-only accounts) — note in output but continue
```

---

## STEP 2 — ANALYSE BENCHMARK VIDEO SCRIPTS

From the transcriptions, identify:

```
HOOK PACING: how many words in the first 5 seconds of top performers?
(target range: 15-35 words spoken in 3-5 seconds)

HOOK ENTRY STYLE: does the top video start mid-action, with a statement, or a question?

ENERGY LEVEL: calm confessional / direct address / urgent / conversational

BODY STRUCTURE: how is the body copy delivered?
(short punchy sentences / longer narrative / list format / back-and-forth)

CTA PHRASING: exact CTA words from the top video — replicate, don't improvise

STAGING PATTERNS from top videos (if staging is visible from context):
Does the transcript suggest a location? ("I was in the ute when I figured this out...")
Does it reference props? ("I was looking at this invoice...")
```

---

## STEP 3 — GENERATE VIDEO SCRIPTS

One complete script per hook variant. 10 hooks per concept × 2 concepts = 20 scripts per funnel.

### Script structure

```
━━━ HOOK STAGING ━━━

LOCATION:
[Exactly where the person is — one specific sentence.
 Must feel instantly authentic to the target niche — no studios, no cafés.]

PROP:
[What they are holding or interacting with — one specific sentence.
 Must be an everyday niche-relevant item, not staged or placed for effect.]

ACTION:
[What they are doing as they begin to speak — one specific sentence.
 Must be subtle and interruptible — as if the camera caught them mid-task.
 CANNOT block speech — see blocked actions list below.]

DIRECTOR'S NOTE:
[One sentence — the visual mood in the first 2 seconds.
 What does the viewer see before the person opens their mouth?]

━━━ SPOKEN SCRIPT ━━━

[HOOK — spoken first, 0:00–0:05]
"[exact hook text from Skill 2 — word for word, no changes]"

[BODY — 0:05–0:35 approx]
"[body copy from Skill 2, broken into natural spoken units.
  New line = natural breath/pause point.
  Short sentences on their own line.
  Longer narrative broken mid-thought where a person would naturally pause.]"

[CTA — final 5-10 seconds]
"[CTA — exact phrasing from winner transcripts where available.
  Simple, direct, single action: 'Link in the ad — free calculator, 30 seconds.']"

━━━ PRODUCTION NOTES ━━━

Estimated duration: [X] seconds (at ~130 words/min natural pace)
Energy: [calm / medium / urgent]
Hook type: [continuer / explorer]
Suggested edit point: [if body is long, note where a natural b-roll cut could go]
```

---

## HOOK STAGING RULES (mandatory)

### Niche-authentic locations (trades business owners)

✅ Use:
- White ute/HiLux/Ranger cab — parked, engine off, morning light
- Residential job site — timber frame, brick veneer, concrete slab, fresh excavation
- Site shed / office — functional, lived-in, paperwork on desk
- Workshop / garage — tools visible, concrete floor, fluorescent lighting
- Ute tailgate / tray — end of day, tools being loaded or unloaded
- Kitchen table — late night, paperwork spread out, overhead light

❌ Never use:
- Coffee shop / café
- Generic office with monitor and desk
- Gym or outdoor fitness setting
- Anywhere that looks set up for filming
- Anywhere that doesn't exist in a trade business owner's working day

### Niche-authentic props

✅ Use (condition matters — worn and used, not showroom new):
- Clipboard with handwritten quote or job card
- Hard hat — held, not worn during speech
- High-vis vest — over shirt or folded under arm
- Specific trade tool held loosely (not being operated)
- Set of keys — ute keys, site keys
- Takeaway coffee cup — not being drunk from (see blocked actions)
- Printed invoice or quote document
- Phone/tablet showing a relevant screen (invoice, spreadsheet, calculator)
- Work gloves tucked in belt or held

❌ Never use:
- Professional microphone or camera equipment (breaks authenticity)
- Generic office supplies (pen and notepad alone)
- Anything that required setup to place in shot
- Anything that doesn't belong in the target audience's actual work life

### Actions (interruptible and speech-compatible)

✅ Use:
- Looking at clipboard / quote / invoice → glances up to camera
- Scrolling on phone screen → pauses and looks up
- Walking toward camera from site background → pauses and speaks
- Loading tools into ute tray → stops and turns to camera
- Sitting in ute, keys visible → doesn't start the car, turns to speak
- Checking a measurement on tape → looks up
- Leaning against ute with arms crossed → uncrosses and speaks

❌ Blocked actions (cannot block speech or create noise):
- Drinking anything — mouth occupied
- Eating anything — mouth occupied
- Operating power tools — too loud, cannot speak
- Talking on phone — creates confusion about who they're speaking to
- Driving — safety issue + can't look at camera
- Hammering, sawing, drilling — too loud
- Any action requiring sustained physical effort (carrying heavy object, climbing)

### Auto-validation

```python
BLOCKED = [
    "drinking", "sipping", "eating", "chewing",
    "drilling", "hammering", "sawing", "operating",
    "driving", "on the phone", "on a call", "on his phone", "on her phone"
]

def validate_action(action_text: str) -> bool:
    return not any(b in action_text.lower() for b in BLOCKED)

# If validation fails: regenerate action. Log the failure.
```

---

## STEP 4 — SAVE TO SUPABASE

```sql
CREATE TABLE ad_video_scripts (
    script_id         VARCHAR(64) PRIMARY KEY,
    -- e.g. "PT_LABOUR_C1_A_H1_VID"
    concept_id        VARCHAR(64) NOT NULL REFERENCES ad_concepts(concept_id),
    body_ref          CHAR(1) NOT NULL,       -- 'A' or 'B'
    hook_index        SMALLINT NOT NULL,      -- 1 to 5
    hook_type         VARCHAR(16),            -- 'continuer' or 'explorer'
    hook_text         TEXT NOT NULL,          -- exact spoken hook
    location          TEXT NOT NULL,
    prop              TEXT NOT NULL,
    action            TEXT NOT NULL,
    directors_note    TEXT,
    full_script       TEXT NOT NULL,          -- complete teleprompter script
    estimated_seconds SMALLINT,
    energy_level      VARCHAR(16),            -- 'calm' / 'medium' / 'urgent'
    created_at        TIMESTAMPTZ DEFAULT NOW()
);
```

---

## STEP 5 — OUTPUT FORMAT (markdown doc for team)

```markdown
# Video Script Brief — [FUNNEL] — Week of [DATE]
Account: [account_id] | Generated: [timestamp]

---

## VIDEO BENCHMARKS (All-Time Top Performers)

| Rank | CPL | Hook (first 10 words) | Energy | Duration |
|------|-----|-----------------------|--------|----------|
| 1 | $1.80 | "I worked 237 days straight, my wife..." | Calm/confessional | ~45s |

**Staging patterns from top videos:** [any staging cues identified from transcripts]
**CTA phrasing to replicate:** "[exact CTA from top video]"

---

## VIDEO SCRIPTS

---

### C1_A_H1 — Continuer | Body A | Hook 1
**concept_id:** PT_LABOUR_C1_2026W10

---

🎬 **HOOK STAGING**

**LOCATION:** Sitting in the driver's seat of a white HiLux, parked outside a residential job site. Engine off. Morning sun through the windscreen. Street quiet.

**PROP:** A printed quote sheet on a clipboard resting on the steering wheel — numbers visible but not legible, clearly a trade quote.

**ACTION:** Running a finger down a column of figures on the quote sheet. Pauses. Looks directly into camera.

**DIRECTOR'S NOTE:** The viewer sees a tradie doing his numbers before the day starts. Instantly familiar to any trades business owner.

---

🎙️ **SPOKEN SCRIPT**

**[HOOK — 0:00–0:05]**
"I worked 237 days straight. My wife went to bed alone most nights."

**[BODY — 0:05–0:35]**
"My kids called me Daddy Always Working.

I wasn't lazy. I wasn't disorganised.

I was just busy working — for basically nothing.

Turns out I'd been undercharging for years.

Not by a little — by a lot.

My real hourly cost was $94. I was charging $68.

Every hour I worked, I was going backwards.

The day I calculated my real number was the day everything changed."

**[CTA — 0:35–0:45]**
"There's a free calculator in the link — takes 30 seconds. Put your numbers in. See your real cost. Most tradies are shocked by what it says."

---

📋 **PRODUCTION NOTES**
- Estimated duration: ~42 seconds
- Energy: calm, confessional
- Hook type: Continuer (retains "237 days straight" from $1.80 CPL winner)
- Edit point: natural pause after "for basically nothing" — b-roll cut option here

---

### C1_A_H2 — Continuer | Body A | Hook 2
[same structure]

---

[... 20 scripts total ...]

---
*script_ids saved to Supabase: ad_video_scripts*
```

---

## COMBINED MASTER BRIEF

All 4 skills combine into one master Creative Brief per funnel:

```
/Users/atlas/reports/{client_slug}/creative_brief_{funnel}_{week_start}.md
```

```
CONCEPT C1 — "[Name]"
Headline | Source ads with CPL

  AD VARIANT C1_A_H1 — Continuer
  ├── COPY: Body A + Hook 1 (from Skill 2)
  ├── IMAGE A: [JSON prompt] (from Skill 3)
  ├── IMAGE B: [JSON prompt] (from Skill 3)
  └── VIDEO: [staging + full script] (from Skill 4)

  AD VARIANT C1_A_H2 — Continuer
  [same structure]

  AD VARIANT C1_A_H3 — Explorer
  [same structure]

  [... through C2_B_H5 ...]
```

One file. Everything matched by concept_id. Copy + image + video are always in sync.

---

## EDGE CASES

| Situation | Handling |
|-----------|----------|
| No video transcriptions (image-only account) | Generate staging from copy context + audience knowledge; note "No video benchmarks available" |
| Action fails validation | Regenerate; log original + replacement |
| Hook > 35 words (may be too long for 3-5 second delivery) | Flag: "HOOK MAY EXCEED 5 SECONDS — consider trimming for video use" |
| Hook text not found in ad_concepts | Error: Skill 2 data incomplete |

---

## IMPROVEMENT BACKLOG

- [ ] Auto-estimate duration: count words / 130 × 60 → seconds
- [ ] B-roll shot list: 5 suggested b-roll shots per script
- [ ] UGC persona matching: tag scripts for specific persona types (sole trader / 3-5 person crew / 10+ person business)
- [ ] Track which scripts get filmed and tested; CPL back into Skill 1's winner pool
- [ ] Add "director's brief" document: one-pager for the person filming, no technical jargon

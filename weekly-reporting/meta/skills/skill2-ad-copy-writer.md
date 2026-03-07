# SKILL 2: Ad Copy Writer
**Version:** 2.0 | **Part of:** Creative Intelligence Suite (Skill 2 of 4)

---

## PURPOSE

Read proven winners from Skill 1 (Supabase). Write 2 new main body ad copies with 5 hooks each, per funnel. Every hook is grounded in what has already worked — but the portfolio is split between **Continuers** (exploit what works) and **Explorers** (hunt the next winner).

Does not touch the Meta API. Reads only from Supabase.

**Run order:** Runs second. Requires Skill 1 to have completed for this funnel/week.

---

## THE CORE CREATIVE PRINCIPLE — CONTINUERS vs EXPLORERS

In a healthy ad account, you never launch only untested creative. If every ad in a batch is new and experimental, and none of them work, the account stalls — there is no floor.

The solution is a portfolio approach to every creative batch:

**CONTINUERS (H1-H2 per body copy):**
Hooks that are almost identical to the proven winner. Same opening line, same emotional entry point, same core structure. Retain what is already working. These combat creative fatigue — the same message refreshed slightly continues to perform for the same audience. Because they are grounded in a proven format, their probability of success is high. They are the floor.

**EXPLORERS (H3-H5 per body copy):**
Hooks built on the same emotional foundation as the winners but exploring a new angle, new specific detail, or new entry point into the same pain. These are the ceiling hunt — one of these becomes next week's winner. They are grounded enough to have a reasonable success rate, but they push into new territory. They are the upside.

**The ratio:** 2 Continuers + 3 Explorers per body copy, per concept.
The account always has proven creative in-market while the explorers hunt.

---

## WHEN TO USE

- Run every Monday at 4am AEDT, after Skill 1 completes
- Can be run on-demand if Skill 1 data exists in Supabase for the target funnel/week

---

## INPUTS / CONFIGURATION

```python
CONFIG = {
    "account_id": "act_559512967808213",
    "funnel_name": "labour_calc",
    "week_start": "2026-03-10",
    "output_dir": "/Users/atlas/reports/{client_slug}/"
}
```

---

## STEP 1 — READ WINNERS FROM SUPABASE

```python
# Read top copy winners (image + video captions)
copy_winners = supabase.table("ad_copy_winners") \
    .select("*") \
    .eq("account_id", account_id) \
    .eq("funnel_name", funnel_name) \
    .eq("week_start", week_start) \
    .order("cpl", desc=False) \
    .execute().data

# Read video transcriptions
transcriptions = supabase.table("ad_video_transcriptions") \
    .select("*") \
    .eq("account_id", account_id) \
    .eq("funnel_name", funnel_name) \
    .eq("week_start", week_start) \
    .order("cpl", desc=False) \
    .execute().data

# Abort if nothing to work from
if not copy_winners and not transcriptions:
    raise RuntimeError("Skill 1 has not run for this funnel/week. Run ad-winner-extraction first.")
```

**Priority order for analysis:**
1. Video transcriptions (spoken scripts — these are the actual words that drove conversions)
2. Written captions from image ads (supporting reference)

---

## STEP 2 — ANALYSE WINNERS

Before writing anything, identify the following patterns across the combined pool:

```
HOOK PATTERNS
- What are the first 10 words of each top performer? (written + spoken)
- What format? (personal story / stat / confession / challenge / question)
- What emotional trigger? (family sacrifice / financial loss / identity / fear / aspiration)

SPECIFICITY SIGNALS
- What exact numbers, timeframes, dollar amounts appear in top hooks?
- These are to be reused as-is in Continuer hooks — the specificity IS the proof

NICHE IDENTIFICATION METHOD
- Does the top hook name the niche directly? ("tradie", "plumber")
- Or does it use niche-specific actions/pains? ("worked 237 days straight")
- Which has the lower CPL? → Use that method for all new hooks

LANGUAGE REGISTER
- Formal vs casual? (listen to transcripts especially)
- Trade-specific jargon used? (charge-out rate, quote, SWMS, on the tools)
- Sentence length? (short punchy vs. longer narrative)

CTA PATTERN
- What exact CTA phrase appears in top performers?
- Replicate exactly — do not improvise the CTA
```

---

## STEP 3 — WRITE NEW COPY

### Output structure: 2 concepts (C1, C2)

Each concept:
- `concept_id` — e.g. `PT_LABOUR_C1_2026W10`
- `headline` — 1 per concept (≤10 words, specific, benefit-driven)
- `body_a` — 150-200 words
- `hooks_a` — 5 hooks: H1-H2 (Continuers) + H3-H5 (Explorers), 35-55 words each
- `body_b` — 150-200 words
- `hooks_b` — 5 hooks: H1-H2 (Continuers) + H3-H5 (Explorers), 35-55 words each
- `source_refs` — which winner ads inspired this concept (ad_id + CPL)

---

### PROMPT TEMPLATE

```
You are a direct response copywriter for Facebook/Instagram ads targeting [AUDIENCE].
Offer: [OFFER_NAME] — [OFFER_DESCRIPTION]

━━━ SOURCE MATERIAL — READ CAREFULLY ━━━

PRIORITY SOURCE — VIDEO AD TRANSCRIPTS (these are the actual spoken words driving results):

VIDEO #1 | CPL: $[X] | [N] leads | $[SPEND] spend
Hook (first spoken line): "[hook_text]"
Full transcript:
"""
[full_transcript]
"""

VIDEO #2 | CPL: $[X] | [N] leads | $[SPEND] spend
Hook: "[hook_text]"
Full transcript:
"""
[full_transcript]
"""

[up to 5 transcripts]

SUPPORTING SOURCE — IMAGE AD CAPTIONS:

IMAGE #1 | CPL: $[X] | [N] leads
Headline: [title]
Caption: [body_copy]

[up to 5 captions]

━━━ YOUR TASK ━━━

Write 2 new main body copies (150-200 words each) with 5 hooks per body (35-55 words each).

CONTINUER HOOKS (H1 and H2 for each body):
These should be almost identical to the proven winners above — same opening line, same emotional entry point, same structure. The audience has already responded to this. You are retaining what works.
Do not reinvent. Do not "improve". Retain.
The only acceptable changes:
  - Slightly different specific detail (different number, different timeframe) while keeping the emotional beat identical
  - Equivalent opening line that creates the same emotional response
  - The core structure and entry point must be preserved

EXPLORER HOOKS (H3, H4, and H5 for each body):
These should be built on the same emotional foundation as the winners but explore a new entry point.
Same pain, same audience, same offer — different angle into the conversation.
Ask: what is another way someone in this audience might be feeling this same pain right now?
What is a different specific moment or detail that triggers the same realisation?

MANDATORY RULES — apply to ALL hooks:
1. First 10 words must signal the target audience WITHOUT naming them directly or using "are you a [niche]?"
   Use the actions, pains, or specific language of their world instead.
2. Be specific. Use real numbers, timeframes, dollar amounts from the source material above.
   For Continuer hooks, retain the exact numbers from the winners. Do not round or generalise.
3. 150-200 words for body copies. 35-55 words for hooks. Count them.
4. Write how the audience talks. No corporate language. Model the register from the transcripts.
5. Each hook flows naturally into the body copy.
6. One headline per concept (≤10 words, specific, benefit-driven).
7. Note which source ad(s) inspired each concept.

━━━ OUTPUT FORMAT ━━━

CONCEPT C1 — "[Name]"
INSPIRED BY: [source ad name/id and CPL]
HEADLINE: [headline]

BODY A ([word count] words):
[body copy]

HOOK A1 — CONTINUER ([word count] words):
[hook — almost identical to top winner]

HOOK A2 — CONTINUER ([word count] words):
[hook — almost identical to top winner, slight variation]

HOOK A3 — EXPLORER ([word count] words):
[hook — same emotional foundation, new angle]

HOOK A4 — EXPLORER ([word count] words):
[hook — same emotional foundation, different entry point]

HOOK A5 — EXPLORER ([word count] words):
[hook — same emotional foundation, new specific detail or scenario]

BODY B ([word count] words):
[body copy]

HOOK B1 — CONTINUER: [hook]
HOOK B2 — CONTINUER: [hook]
HOOK B3 — EXPLORER: [hook]
HOOK B4 — EXPLORER: [hook]
HOOK B5 — EXPLORER: [hook]

---

CONCEPT C2 — "[Name]"
[same structure]
```

---

## STEP 4 — SAVE TO SUPABASE

```sql
CREATE TABLE ad_concepts (
    concept_id        VARCHAR(64) PRIMARY KEY,
    -- e.g. "PT_LABOUR_C1_2026W10"
    account_id        VARCHAR(32) NOT NULL,
    funnel_name       VARCHAR(128),
    week_start        DATE NOT NULL,
    headline          TEXT,
    body_a            TEXT,
    body_b            TEXT,
    hooks_a           JSONB,   -- [{index:1, type:"continuer", text:"..."}, ...]
    hooks_b           JSONB,
    source_refs       JSONB,   -- [{ad_id, cpl, type:"video"|"image"}]
    created_at        TIMESTAMPTZ DEFAULT NOW()
);
```

Hook JSON structure:
```json
[
  {"index": 1, "type": "continuer", "text": "I worked 237 days straight...", "word_count": 42},
  {"index": 2, "type": "continuer", "text": "My wife went to bed alone...", "word_count": 38},
  {"index": 3, "type": "explorer",  "text": "My bookkeeper told me something...", "word_count": 44},
  {"index": 4, "type": "explorer",  "text": "I quoted 40 jobs last month...", "word_count": 41},
  {"index": 5, "type": "explorer",  "text": "Tuesday morning, 6am...", "word_count": 39}
]
```

---

## STEP 5 — OUTPUT FORMAT (markdown doc for team)

```markdown
# Ad Copy Brief — [FUNNEL] — Week of [DATE]
Account: [account_id] | Generated: [timestamp]

---

## WINNER ANALYSIS (Source Material)

### Top Video Ad Transcripts (Priority Source)

**#1 — $[CPL] CPL | [N] leads | $[SPEND] spend**
Hook: "[hook_first_10]..."
[full transcript in blockquote]

**#2 — [same]**

### Top Image Ad Captions (Supporting Source)

**#1 — $[CPL] CPL | [N] leads**
Headline: [title]
Caption: [body_copy]

---

## PATTERNS IDENTIFIED
- Hook format: [e.g. personal sacrifice story → revelation → solution]
- Niche signal method: [e.g. action-based — "237 days straight" not "tradie"]
- Key specificity signals: [numbers, timeframes that must be retained]
- Language register: [e.g. casual, direct, first-person confession]
- CTA: [exact CTA phrase from winners]

---

## NEW CONCEPTS

### CONCEPT C1 — "[Name]"
**Inspired by:** [source] | **Headline:** [headline]

**BODY A** ([N] words)
[body copy]

**H1 — CONTINUER** ([N] words)
[hook]
*Why: Retains the "[exact opening pattern]" entry point from [source ad] at $[CPL] CPL*

**H2 — CONTINUER** ([N] words)
[hook]
*Why: [brief note on what is retained vs slightly adjusted]*

**H3 — EXPLORER** ([N] words)
[hook]
*Why: Same [emotional trigger] but enters via [new angle]*

**H4 — EXPLORER** ([N] words)
[hook]

**H5 — EXPLORER** ([N] words)
[hook]

---

**BODY B** ([N] words)
[body copy]

**H1-H5:** [same structure]

---

### CONCEPT C2 — "[Name]"
[same structure]

---
*concept_ids saved to Supabase: ad_concepts*
*Ready for Skill 3 (Image) and Skill 4 (Video)*
```

---

## EDGE CASES

| Situation | Handling |
|-----------|----------|
| No transcriptions available (video-free account) | Run on captions only; note in output |
| Hook word count outside 35-55 | Flag in output; do not auto-trim (may affect meaning) |
| Body copy outside 150-200 words | Flag in output; regenerate if >10% off target |
| Continuer hook too identical to source (word-for-word copy) | Regenerate with instruction to vary while retaining structure |
| No qualifying ads at all | Abort: "Insufficient data — Skill 1 found no qualifying ads" |

---

## IMPROVEMENT BACKLOG

- [ ] Auto-score Continuer hooks: similarity score vs source (should be >70% similar, not 100%)
- [ ] Track which hooks actually get tested each week and which CPL they achieve
- [ ] Feed tested hook performance back into next week's Continuer selection
- [ ] Persona variant: flag if the audience has distinct sub-segments (e.g. sole traders vs. 5+ person businesses) and write targeted variants
- [ ] Hook length validation: auto-count words before saving, reject if out of range

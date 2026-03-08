# Copy Rules Reference

Full rules for generating ad copy via Skill 2. These rules are injected into the GPT-4o system prompt and enforced during output validation.

---

## The #1 Rule: Signal the Niche, Never Name It

**First 10 words must identify the reader through action or pain — never by calling them out.**

| ✅ CORRECT | ❌ WRONG |
|-----------|---------|
| "I worked 237 days straight before I figured this out" | "Are you a trades business owner?" |
| "My apprentice asked me why I charged $68 when the job cost $94" | "If you run a trade business, listen up" |
| "Settlement fell through on a Friday. I had 3 clients waiting." | "Attention mortgage brokers" |
| "The vendor knocked back offer #3 and my vendor was ready to walk" | "Real estate agents, this is for you" |

**Why:** Naming the audience looks like an ad. The right person recognising themselves through a situation is native content.

---

## Hook Rules

### Rule 1 — Niche Signal in First 10 Words
As above. The hook must be self-filtering. The right audience recognises themselves; everyone else scrolls past.

### Rule 2 — Continuers Retain Exact Numbers
If the winning hook says "237 days straight", Continuers must use 237 — not "nearly a year" or "almost 8 months". Exact numbers are part of the authenticity signal. Changing them changes the ad.

### Rule 3 — Explorers Use the Same Emotional Foundation
Explorers must carry the same emotional tension as the winner — but through a different door. Same feeling (exhaustion, discovery, injustice, urgency), different situation.

**Example:**
- Winner hook: "I worked 237 days straight before I figured out why I was still broke"
- Explorer variant: "My apprentice asked me how much I made per hour. I didn't know the answer."

Both carry the same tension (financial insecurity despite being busy) — different entry point.

### Rule 4 — Word Count: 35–55 Words
Count every word. If the hook is under 35 words it's not delivering enough setup. Over 55 words and the first drop-off happens before the body loads.

### Rule 5 — No Corporate Language
Forbidden words and phrases:

```
leverage, optimise, optimise, implement, empower, synergise, scalable,
drive results, unpack, deep dive, actionable, utilise, streamline,
game-changer, best-in-class, cutting-edge, revolutionary, disruptive,
at the end of the day, moving the needle, circle back, bandwidth
```

If GPT-4o uses any of these, reject the output and regenerate.

### Rule 6 — CTA is Fixed
The CTA (call-to-action) must replicate the **exact phrase** from the winning ad. Do not improvise. If the winner says "Click the link below and grab the free Labour Rate Calculator", that is the CTA for all variants in this batch.

---

## Body Rules

### Word Count: 150–200 Words
Count every word. Under 150 = not enough social proof or mechanism. Over 200 = scroll fatigue on mobile.

### Structure
Good body copy structure (in order):
1. **Expand the hook** — give the story behind the situation
2. **Identify the problem mechanism** — why does this happen?
3. **Introduce the solution** (brief) — what changed?
4. **Social proof** — what happened after?
5. **CTA** — exact winner phrase

### Tone
- First person (I/my/we) wherever possible
- Conversational — write how a person talks, not how a copywriter writes
- Specific — exact numbers, timeframes, job types
- No passive voice

---

## Niche Signal Examples by Audience

### Trades Business Owners (Profitable Tradie)
- Dollar amounts: `"charged $68 but real cost was $94"`, `"$30k sitting in unpaid invoices"`
- Time signals: `"237 days straight"`, `"6 days a week for 3 years"`
- Situations: `"my apprentice asked"`, `"the quote came back wrong"`, `"invoice sent on Friday"`, `"job cost calculator told me"`
- Roles: apprentice, estimator, project manager (never "employee" or "team member")

### Mortgage Brokers (Strategic Mortgage Brokers)
- Situations: `"settlement fell through"`, `"rate lock expired"`, `"pre-approval lapsed"`, `"bank knocked back on day of settlement"`
- Dollar amounts: `"$430k loan"`, `"0.3% difference"`, `"$18/month"`
- Urgency signals: `"3pm Friday"`, `"settlement in 4 days"`, `"unconditional by Tuesday"`

### Real Estate Agents
- Situations: `"listing sat for 90 days"`, `"vendor knocked back 3 offers"`, `"open home — 4 groups, 0 offers"`
- Signals: `"auction passed in"`, `"price reduction 3 weeks in"`, `"vendor dropped $40k"`

### General (if no niche-specific account)
- Use specific dollar amounts, timeframes, job titles relevant to that industry
- Never use generic pain: "Are you struggling with X?" → rewrite as situation

---

## Validation Checklist (run before saving to Supabase)

- [ ] Hook word count: 35–55
- [ ] Body word count: 150–200
- [ ] First 10 words signal niche via action or pain (not by naming audience)
- [ ] No forbidden corporate language
- [ ] Continuer hooks (H1/H2): retain exact numbers from winning hook
- [ ] Explorer hooks (H3/H5): same emotional tension, different situation
- [ ] CTA matches exact winner CTA phrase
- [ ] Tone is conversational, first-person, specific

---

## GPT-4o Rejection Criteria

Reject and regenerate if:
1. Any hook starts with "Are you a..." or "If you're a..." or names the audience directly
2. Body word count outside 150–200 range
3. Hook word count outside 35–55 range
4. Any forbidden corporate language found
5. CTA is improvised (different from winner CTA)
6. Continuer hook (H1/H2) doesn't retain exact numbers from winner

# Image Formats Reference

Catalogue of proven ad image formats used by this pipeline. Each format includes performance data (where available), best-use context, and critical rules. Skill 3 uses this reference to assign Option A and Option B formats to each ad variant.

---

## How Formats Are Assigned

- **Option A** → the format used by the lowest-CPL image ad in the funnel (as analysed by Skill 1)
- **Option B** → the next best format, or a deliberately contrasting format for pattern interrupt testing
- Format names must match the `image_format` field in `ad_image_winners` exactly

---

## FORMAT 1: Reddit Post Screenshot

**What it is:** An authentic-looking Reddit post screenshot in dark or light mode UI. The post reads like a genuine community confession, discovery, or question. No visible branding.

**Performance data (Profitable Tradie):**
- Labour Calc funnel: **$1.80 CPL** (top performer across all formats)
- Pricing Calc funnel: **$5.86 CPL**

**Best used for:**
- Social proof hooks ("I found a tool that changed how I price jobs")
- Confession hooks ("I didn't know my real cost until...")
- Discovery story hooks ("Someone in this thread asked a question I couldn't answer")

**Critical rules:**
- Username must be authentic-sounding for the niche (e.g. `concreter_QL_travis`, `plumber_brisbane_82`)
- Upvote count: 400–900 (too low = no credibility; too high = looks viral/fake)
- Comments count must be visible (typically 12–40)
- Post body must be 3–5 paragraphs — full story, not truncated
- Post must be in a realistic-sounding subreddit (e.g. `r/AussieTrades`, `r/tradie`)
- Do not include award icons unless it looks authentic
- Light mode vs dark mode: test both; dark mode tends to perform better on dark feeds

**AI generation notes:**
- Font: Reddit's IBM Plex Sans or system default
- Background: near-black (#1A1A1B) for dark mode
- Post upvote arrows: use Reddit's triangle design, orange when upvoted

---

## FORMAT 2: Whiteboard

**What it is:** A real-looking whiteboard in a trade environment — workshop, site shed, or training room. Text is handwritten (looks handwritten), not printed. Content is a list, calculation, or statement relevant to the hook.

**Performance data (Profitable Tradie):**
- CPL range: **$2.51–$4.00** across PT funnels

**Best used for:**
- Rant or call-out hooks ("Here's what nobody tells you about pricing a job")
- Team communication angle ("What I wrote on the whiteboard at our Monday meeting")
- "Listen up" messages from the business owner

**Critical rules:**
- Writing must look genuinely hand-drawn — no perfect letter spacing, no printed fonts
- Include marker artefacts (slight bleed, inconsistent pressure)
- Background must be trade-appropriate: concrete floor, tool rack, shelving visible
- No branded merchandise visible on the whiteboard
- Include one or two erased marks for authenticity

**AI generation notes:**
- Lighting: natural/industrial — no studio softbox look
- Whiteboard should be slightly dirty (eraser marks, ghosting from previous writing)
- Text content on whiteboard should be directly related to the hook

---

## FORMAT 3: Phone Screenshot (Notes App)

**What it is:** An iPhone Notes app screenshot in dark mode showing a checklist or short notes. Looks like a genuine personal note the creator is sharing. Authenticity signals are critical.

**Performance data (Profitable Tradie):**
- Systems Blueprint funnel: **$9.34 CPL** — #1 performing image in that funnel

**Best used for:**
- "Here's what I use" authentic sharing hooks
- Checklist/system reveal hooks ("I wrote down every step I follow")
- "I didn't think I'd share this" hooks

**Critical rules:**
- Must include authenticity signals:
  - Unread badge count must be low (1–4 unread messages visible in status bar)
  - PDF attachment icon visible if relevant
  - Real checklist items — not generic placeholder text
  - Time shown in status bar should be realistic (not 9:41 — Apple's demo time is too recognisable)
- Dark mode only (light mode performs significantly worse for this format)
- Notes app font must match iOS default (SF Pro)

**AI generation notes:**
- Status bar: include battery %, signal bars, Wi-Fi — all must look realistic
- Note content must be directly tied to the hook's topic
- Include at least 2 checked items and 3 unchecked items if checklist format

---

## FORMAT 4: Google Sheets / Spreadsheet Screenshot

**What it is:** A screenshot of an actual calculator or spreadsheet — looks like the creator is sharing their real working tool. Red annotations (circles, arrows) are added to highlight the key number.

**Performance data (Profitable Tradie):**
- Labour Calc funnel: **$2.51 CPL** — #2 image in that funnel

**Best used for:**
- Tool demonstration hooks ("I built a calculator that does this automatically")
- Real numbers hooks ("Here's what the numbers actually look like")
- "Charged $68 but the real cost was $94" style reveal hooks

**Critical rules:**
- Numbers must be real and specific — not round numbers or obvious placeholders
- Red circle or arrow annotation is mandatory (it's a credibility signal)
- Spreadsheet must look functional — column headers, multiple rows visible
- Formula bar visible if possible (proves it's a real working spreadsheet)
- No branding in the spreadsheet itself

**AI generation notes:**
- Use Google Sheets dark or light theme
- Include at least one cell with a formula visible
- Annotation style: red circle drawn by hand (not perfect), red arrow pointing to key result

---

## FORMAT 5: Flat-Lay

**What it is:** An overhead photo of a printed document on a workbench or desk, surrounded by trade tools. Looks like the creator printed something out and placed it in their workspace.

**Performance data:** Currently in testing across PT funnels.

**Best used for:**
- Physical/tangible angle ("I printed this out and stuck it to the wall")
- "I've been using this for 6 months" authenticity hooks
- Checklist or guide reveals

**Critical rules:**
- Worn, real trade tools — no pristine hardware store props
- Real surface — concrete, timber, painted steel, not a studio desk
- Printed document must have visible text that matches the hook topic
- No studio lighting — natural or workshop ambient light only
- One or two props maximum — don't overcrowd the frame

---

## FORMAT 6: Meme

**What it is:** Classic meme format — stock image (ideally trade-related) with bold white Impact-font text bars at the top and bottom. Relatable frustration or situation.

**Performance data:** Context-dependent — strong for frustration and rant hooks.

**Best used for:**
- Frustration hooks ("When you've been fully booked for 6 months but still can't afford to pay yourself")
- Relatable failure scenarios specific to the niche
- Pattern interrupt on value-heavy feeds

**Critical rules:**
- Must be highly specific to the niche situation — not generic business frustration
- Image must be instantly recognisable as trade/industry relevant (or deliberately absurdist)
- Text must be punchy — 5–8 words top, 5–8 words bottom
- Font: Impact or Anton (Google Fonts) — white text, black outline

---

## FORMAT 7: B&W Photo

**What it is:** The exact same ad as a colour photo version — but fully desaturated to black and white. Used as a pattern interrupt on colour-heavy feeds.

**Performance data:** Typically tested as Option B alongside a colour version.

**Best used for:**
- Pattern interrupt on colour-heavy feeds
- Serious/urgent emotional tone
- When the colour version is underperforming and you need a quick test variant

**Critical rules:**
- Must be editorial B&W quality — not faded, not sepia, not low contrast
- Full desaturation only — maintain contrast and shadows
- Same composition as the colour version — this is not a different concept
- Never use B&W for meme format (loses impact font readability on dark feeds)

---

## Format Selection Logic (Skill 3)

```python
# Option A = winner format
winner_format = ad_image_winner["image_format"]  # from Supabase

# Option B = next best performing format that is NOT Option A
alternate_format = get_alternate_format(
    winner_format=winner_format,
    available_formats=FORMAT_PERFORMANCE_ORDER,
    hook_type=hook.type,  # continuer vs explorer
)
```

**Default format performance order (Profitable Tradie):**
1. Reddit Post Screenshot ($1.80 CPL)
2. Google Sheets / Spreadsheet ($2.51 CPL)
3. Whiteboard ($2.51–$4.00 CPL)
4. Phone Screenshot/Notes App ($9.34 CPL in sys_blueprint)
5. Flat-Lay (testing)
6. Meme (context-dependent)
7. B&W Photo (pattern interrupt)

> Performance order is funnel-specific. Always use the actual CPL data from `ad_image_winners` for the current account/funnel rather than this default order.

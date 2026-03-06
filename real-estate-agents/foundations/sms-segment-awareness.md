# SMS Segment Awareness

## Purpose
Optimize message length for cost and engagement. SMS character limits directly impact both cost and readability.

## Rules

### Character Limits
- 1 SMS segment = 160 characters (GSM-7 encoding, which we use since NO emojis)
- 2 segments = 306 characters (not 320 - there's overhead for concatenation headers)
- 3 segments = 459 characters

### Strategy
- Some messages should be punchy single-segment (under 160 chars) - especially for re-engagement, pattern interrupts, and ultra-short angles
- Longer messages (2 segments, ~250-300 chars) are fine for value-adds and detailed outreach
- RARELY go to 3 segments - only for genuinely information-rich messages

### Important Notes
- The `character_count` in output MUST be accurate
- Include the sign-off in your character count
- The analyst's recommendation should guide length:
  - "ultra-short" → aim for 40-80 chars
  - "value-add" → 160-250 chars is fine

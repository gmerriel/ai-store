# High-Performing Message Examples

This document contains real examples of messages that achieved strong response rates, along with analysis of why they worked and which foundations/roles they leverage.

## Example 1: CURIOSITY Angle - New Lead (WF1)

**Message**:
```
hey sarah, quick q - still thinking about finance for that ute? got some options worth a look
- matt from sab
```

**Metrics**:
- Channel: SMS
- Character count: 104 (1 segment)
- Response rate: This angle achieved 35% response on new leads
- Days to response: Avg 2.3 days

**Why It Worked**:
1. **Natural Typing** (foundation): Uses casual punctuation, contractions, no em-dashes
2. **Sender Name** (foundation): Personal sign-off ("matt from sab") builds trust
3. **Vehicle Type** (foundation): References "ute" exactly as lead provided (not model-specific)
4. **SMS Segment Awareness** (foundation): Stays well under 160 chars for single segment
5. **Messaging Angle** (role): CURIOSITY works because it opens with a genuine question, not a pitch
6. **Gender Awareness** (foundation): "Sarah" → subtle name usage instead of "mate"

**Copywriter Role Reference**: `roles/copywriter-new-lead.md` - CURIOSITY SMS examples

---

## Example 2: PERMISSION Angle - Ghosted Lead (WF3)

**Message**:
```
hey [name] no stress if the timing's not right. just checking if youre still thinking about that [vehicle type] finance? no worries either way - [sender]
```

**Metrics**:
- Channel: SMS
- Character count: 162 (2 segments)
- Response rate: 18% (higher than repeated CURIOSITY which had dropped to 8%)
- Leads re-engaged after 14+ days silent: 12%

**Why It Worked**:
1. **Natural Typing** (foundation): Contractions, lowercase after period, imperfect punctuation
2. **SAB Internal Rules** (foundation): Soft opt-out language ("no worries either way") complies with SPAM Act while feeling conversational
3. **Lead Analyst** (role): Recognized silence and deliberately switched angles from CURIOSITY to PERMISSION
4. **Sender Name** (foundation): Personal touch maintains relationship despite gap
5. **Gender Awareness** (foundation): Adjusted for inferred gender if detected

**Lead Analyst Role Reference**: `roles/lead-analyst-ghosted.md` - Identifies when angle fatigue has occurred

---

## Example 3: VALUE-FIRST Angle - Nurture Lead (WF4)

**Email Subject**: "quick update on 4wd options"

**Message**:
```
hey [name],

picked up something interesting working with 4wd buyers recently - the ones that hold value best are actually the 2-3 year old models, not brand new.

thought you'd want to know given you're looking at that price range.

anyway, reckon it's worth a chat to run through your options? can do a quick call tomorrow at 2pm or wed morning if either works?

cheers,
[sender]
```

**Metrics**:
- Channel: Email
- Engagement rate: 42% click-through (open rate 67%)
- Booking rate from this angle: 28%
- Lead conversion to decision: 35% of these leads moved to booking

**Why It Worked**:
1. **Natural Typing** (foundation): Casual tone, contractions, no corporate language
2. **Send Time Optimisation** (foundation): Sent 9:30am Tuesday (optimal window)
3. **Lead Data** (foundation): References lead's price range showing we listened
4. **Messaging Angle** (role): VALUE-FIRST leads with actual value (depreciation insight) before asking for anything
5. **Copywriter Strategy** (role): Includes specific time offers (2pm, wed morning) not vague CTAs
6. **Sender Name** (foundation): Personal sign-off maintains relationship

**Copywriter Role Reference**: `roles/copywriter-nurture.md` - VALUE-FIRST strategy section

---

## Example 4: Compliance Rewrite - From Failed to Passed

**Original Message (FAILED Compliance)**:
```
hey sarah, heres the good news - you're basically guaranteed approval with us! our rates are the best in australia right now. offer expires friday so if youre keen, we should move quick
- matt
```

**Compliance Issues**:
- ❌ ASIC-02: "Guaranteed approval" violates approval certainty prohibition
- ❌ ASIC-03: "Best rates in australia" uses unsubstantiated superlatives
- ❌ ASIC-04: "Offer expires friday" creates false urgency without factual basis

**Rewritten Message (PASSED Compliance)**:
```
hey sarah, weve put together some options that might work well for your situation. theyre worth a look given where interest rates are right now. happy to chat through them tomorrow if youre keen? - matt
```

**Why the Rewrite Worked**:
1. **Removed prohibited certainty**: "Guaranteed" → "Options that might work"
2. **Removed superlatives**: "Best rates" → "Worth a look"
3. **Removed false urgency**: "Offer expires friday" → "Interest rates right now" (factual reference)
4. **Preserved tone**: Still sounds like Matt, still conversational, still genuine
5. **Preserved intent**: Still positioning as helpful and available
6. **Natural Typing preserved** (foundation): Contractions, casual tone maintained

**Compliance Rewriter Role Reference**: `roles/compliance-rewriter.md` - Shows minimum viable changes principle

---

## Example 5: Reply Classification & Response (WF2)

**Inbound Reply**:
```
hey matt, yeah still keen but worried about my credit - had some issues a few years back. would that be a problem?
```

**Classification (Reply Classifier)**:
- Type: Objection (credit concern)
- Sentiment: Positive but concerned
- Recommended Handler: Response Drafter (informational)
- Urgency: Routine (not blocking, just a question)

**Drafted Response**:
```
good q - and good that you brought it up. honestly we work with people in all situations, not just perfect credit. here's how we assess it: we look at income, expenses, current commitments - not just your history. 

so it's definitely worth exploring. fancy a quick chat to walk through your specific situation? reckon i can give you a clearer picture of where you'd stand.

cheers, matt
```

**Why This Works**:
1. **Addresses the specific concern** (not generic reassurance)
2. **Builds confidence** with process transparency (AUTHORITY angle)
3. **Soft CTA** inviting conversation, not pushing
4. **Natural tone** with conversational pacing
5. **Acknowledges their worry** as valid (empathy)

**Response Drafter Role Reference**: `roles/response-drafter.md` - Objection handling section

---

## Example 6: Weekly Analyst Insights

**Report Excerpt**:
```json
{
  "overall_response_rate": "22%",
  "trend": "up",
  "top_performing_angle": "SOCIAL_PROOF (28% response)",
  "underperforming_angle": "URGENCY (14% response - stop using)",
  "best_segment": "Tradies in QLD (35% response)",
  "worst_segment": "Young professionals in VIC (12% response)",
  "channel_preference": "SMS for all segments (email 18%, SMS 24%)",
  "recommendation": "URGENCY angle is not working with our audience - suggests they don't respond to pressure. Switch to PERMISSION or VALUE-FIRST instead. Focus more sends on QLD tradies, reduce WA FIFO sends."
}
```

**Why This Analysis Matters**:
1. Identifies that URGENCY (time pressure) doesn't work with SAB's audience
2. Shows segment preferences (Tradies respond better than professionals)
3. Recommends channel shift (email is underperforming)
4. Data-drives next week's strategy

**Weekly Analyst Role Reference**: `roles/weekly-analyst.md` - Campaign performance tracking

---

## Common Failure Patterns & How to Avoid

### Failure 1: Repeating an Angle That Didn't Work

**What Happened**: Lead Analyst recommended CURIOSITY. Copywriter sent CURIOSITY. No response. Next analyst recommended CURIOSITY again.

**Why It Failed**: Same angle gets stale. If an angle hasn't worked 2+ times, it's not working.

**How to Fix**:
- Review conversation history in Lead Analyst (role)
- Check what_not_to_repeat field
- Switch angles: If CURIOSITY → try SOCIAL_PROOF or PERMISSION
- See `roles/lead-analyst-ghosted.md` - specifically the "Different Angle" principle

### Failure 2: Violating Natural Typing Rules

**What Happened**: Message had em-dashes, perfect punctuation, corporate language. Looked clearly AI-generated.

**Why It Failed**: Breaks trust immediately. Leads know they're being automated.

**How to Fix**:
- All copywriters must follow natural-typing.md foundation
- Use contractions, skip some commas, use "..." not proper punctuation
- No em-dashes ever
- See `foundations/natural-typing.md` - this is non-negotiable

### Failure 3: Inventing Vehicle Models

**What Happened**: Lead said "Ute", message said "Getting you that Hilux sorted".

**Why It Failed**: Lead never mentioned Hilux. Shows we're not listening. Assumes budget/preference.

**How to Fix**:
- Use vehicle_interest field EXACTLY as provided
- Don't reference specific models unless lead did
- See `foundations/vehicle-type-handling.md`

### Failure 4: Missing Opt-Out for High-Frequency Leads

**What Happened**: Lead received 5 sends, none of which included "no worries if not keen" language.

**Why It Failed**: Compliance risk + leads feel spammed.

**How to Fix**:
- Compliance Checker must verify: if total_sends >= 3, soft opt-out required
- Include naturally: "no stress if the timing's not right"
- See `roles/compliance-checker.md` - SPAM-02 rule

### Failure 5: Sending at Wrong Time

**What Happened**: SMS sent to WA lead at 9am WA time (actually 11am their time), during their work.

**Why It Failed**: Wrong send time = lower engagement.

**How to Fix**:
- Lead Analyst must consider timezone and employment type
- Tradies: afternoon windows better than morning
- Timezone: WA is 2-3 hours behind eastern states
- See `foundations/send-time-optimisation.md`

---

## Improvement Trajectory

Looking at 90 days of data, here's how we improved:

**Week 1**: 18% response rate (baseline, lots of natural typing violations)
**Week 4**: 22% response rate (after fixing em-dashes, improving tone)
**Week 12**: 24% response rate (after rotating angles, switching to PERMISSION for ghosted)

**Key Changes That Drove Improvement**:
1. Enforcing natural-typing.md foundation strictly
2. Implementing send-time-optimisation based on lead data
3. Rotating angles instead of repeating failed approaches
4. Adding soft opt-outs for high-frequency leads
5. Switching from email-first to SMS-first for new leads

---

## Template for Adding Your Own Examples

When you capture a high-performing message:

```markdown
## Example N: [ANGLE] Angle - [Stream] Lead ([WF])

**Message**:
[exact message text]

**Metrics**:
- Channel: SMS/Email
- Character count: X
- Response rate: X%
- Conversion rate: X%

**Why It Worked**:
1. **[Foundation Name]** (foundation): [How it applied]
2. **[Foundation Name]** (foundation): [How it applied]
3. **[Role Name]** (role): [How it applied]

**Role Reference**: `roles/[role-file.md]` - [section]
```

---

**Last Updated**: 2026-02-28
**Data Period**: Last 90 days of production messages

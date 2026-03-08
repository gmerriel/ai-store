# SAB AI Skills - Quick Reference Index

## Foundations (Reusable Rules)
- **natural-typing.md** - No emojis, no em-dashes, imperfect punctuation
- **australian-compliance.md** - ASIC RG234, SPAM Act 2003, ACL, NCC rules
- **sab-internal-rules.md** - Brand voice, SAB-specific messaging constraints
- **vehicle-type-handling.md** - Use vehicle type fields correctly, never invent models
- **sms-segment-awareness.md** - Character limits: 160/306/459
- **gender-awareness.md** - Subtle gender-based language adjustment
- **send-time-optimisation.md** - Best times by day/timezone/employment type
- **sender-name-rules.md** - Personal sign-off requirements
- **lead-data-structure.md** - Fields available in lead records

## Roles (Strategy & Execution)

### Lead Analysts (Strategists)
- **lead-analyst-new-lead.md** - Analyze fresh leads for messaging approach
- **lead-analyst-ghosted.md** - Analyze silent leads for re-engagement
- **lead-analyst-nurture.md** - Analyze engaged leads for next steps

### Copywriters (Message Crafters)
- **copywriter-new-lead.md** - Write messages for newly engaged leads
- **copywriter-ghosted.md** - Write re-engagement messages for silent leads
- **copywriter-nurture.md** - Write guidance messages for engaged leads

### Compliance & Quality
- **compliance-checker.md** - Verify regulatory compliance (ASIC, SPAM Act, ACL, NCC)
- **compliance-rewriter.md** - Rewrite failed messages with minimum changes

### Specialized Roles
- **reply-classifier.md** - Classify inbound lead replies by type/urgency
- **response-drafter.md** - Draft replies to lead questions/objections
- **weekly-analyst.md** - Generate campaign performance insights

## Assembled Messages (Production Ready)

### WF1: New Lead Daily (4am)
- **wf1-lead-analyst.md** - [8.5 KB] Analyze new leads
- **wf1-copywriter.md** - [7.4 KB] Write new lead messages
- **wf1-compliance.md** - [6.6 KB] Check compliance
- **wf1-rewriter.md** - [5.0 KB] Rewrite failed messages

### WF2: Reply Handler (Continuous)
- **wf2-reply-classifier.md** - [2.4 KB] Classify replies
- **wf2-response-drafter.md** - [5.6 KB] Draft responses

### WF3: Ghosted Reactivation (Weekly)
- **wf3-lead-analyst.md** - [7.4 KB] Analyze ghosted leads
- **wf3-copywriter.md** - [6.7 KB] Write re-engagement messages
- **wf3-compliance.md** - [6.8 KB] Check compliance
- **wf3-rewriter.md** - [5.0 KB] Rewrite failed messages

### WF4: Nurture Stream (Daily)
- **wf4-lead-analyst.md** - [7.1 KB] Analyze engaged leads
- **wf4-copywriter.md** - [5.4 KB] Write nurture messages
- **wf4-compliance.md** - [6.8 KB] Check compliance
- **wf4-rewriter.md** - [5.0 KB] Rewrite failed messages

### WF5: Weekly Reporting (Sunday 10am)
- **wf5-weekly-analyst.md** - [1.8 KB] Generate weekly insights

## Code Nodes (n8n JavaScript)
- **build-playbook-context.js** - Merge lead data + strategy (WF1/3/4)
- **collect-contact-ids.js** - Extract contact IDs for batch send (WF1/3/4)

## Templates & Examples
- **high-performing-examples.md** - Real-world successful messages with analysis

## How to Use This Index

1. **To update a rule**: Edit the foundation file (e.g., `foundations/natural-typing.md`)
2. **To change a strategy**: Edit the role file (e.g., `roles/copywriter-ghosted.md`)
3. **To fix compliance**: Edit the compliance foundation or role
4. **To deploy**: The assembled files are what n8n uses (they combine foundations + roles)

All assembled files are marked with:
- Source workflow and node
- Last assembly date (2026-02-28)
- Which foundations they use

For detailed instructions, see README.md

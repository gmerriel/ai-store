# SAB AI Skills Repository

A composable, reusable skill library for Strategic Asset Brokers' AI-driven lead engagement system. This repository decomposes monolithic n8n AI Agent system messages into modular, maintainable foundation and role files.

## What This Is

This is the single source of truth for all SAB AI system prompts. Instead of storing complex system messages inside n8n workflow nodes, we:

1. **Decompose** large system messages into reusable foundation files (shared rules, compliance, data structures)
2. **Extract** role-specific strategies into role files (Lead Analyst, Copywriter, Compliance, etc.)
3. **Assemble** complete system messages by combining foundations + roles
4. **Version control** everything in Git for rollback and audit trails

## Folder Structure

```
sab-ai-skills/
├── foundations/              # Shared rules across all AI agents
│   ├── natural-typing.md              # No emojis, no em-dashes, imperfect punctuation
│   ├── australian-compliance.md       # ASIC RG234, SPAM Act, ACL, NCC rules
│   ├── sab-internal-rules.md          # Brand voice, messaging constraints
│   ├── vehicle-type-handling.md       # Use vehicle_interest field correctly
│   ├── sms-segment-awareness.md       # 160/306/459 character limits
│   ├── gender-awareness.md            # Subtle gender-based language adjustment
│   ├── send-time-optimisation.md      # Day of week, timezone, employment patterns
│   ├── sender-name-rules.md           # Sign-off requirements
│   └── lead-data-structure.md         # Fields available in lead records
├── roles/                   # Role-specific strategies
│   ├── lead-analyst-new-lead.md       # Analyze new leads for messaging angle
│   ├── lead-analyst-ghosted.md        # Analyze ghosted leads for re-engagement
│   ├── lead-analyst-nurture.md        # Analyze engaged leads for next steps
│   ├── copywriter-new-lead.md         # Write messages for new leads
│   ├── copywriter-ghosted.md          # Write re-engagement messages
│   ├── copywriter-nurture.md          # Write nurture/next-step messages
│   ├── compliance-checker.md          # Check messages against regulations
│   ├── compliance-rewriter.md         # Rewrite failed messages with min changes
│   ├── reply-classifier.md            # Classify inbound lead replies
│   ├── response-drafter.md            # Draft replies to lead questions
│   └── weekly-analyst.md              # Generate weekly campaign insights
├── assembled/               # Complete production-ready system messages
│   ├── wf1-lead-analyst.md            # Combined foundations + lead-analyst-new-lead
│   ├── wf1-copywriter.md              # Combined foundations + copywriter-new-lead
│   ├── wf1-compliance.md              # Combined foundations + compliance-checker
│   ├── wf1-rewriter.md                # Combined foundations + compliance-rewriter
│   ├── wf2-reply-classifier.md        # Combined foundations + reply-classifier
│   ├── wf2-response-drafter.md        # Combined foundations + response-drafter
│   ├── wf3-lead-analyst.md            # Combined foundations + lead-analyst-ghosted
│   ├── wf3-copywriter.md              # Combined foundations + copywriter-ghosted
│   ├── wf3-compliance.md              # Combined foundations + compliance-checker
│   ├── wf3-rewriter.md                # Combined foundations + compliance-rewriter
│   ├── wf4-lead-analyst.md            # Combined foundations + lead-analyst-nurture
│   ├── wf4-copywriter.md              # Combined foundations + copywriter-nurture
│   ├── wf4-compliance.md              # Combined foundations + compliance-checker
│   ├── wf4-rewriter.md                # Combined foundations + compliance-rewriter
│   └── wf5-weekly-analyst.md          # Combined foundations + weekly-analyst
├── code-nodes/              # JavaScript code for n8n Code nodes
│   ├── build-playbook-context.js      # Merge lead data + strategy (WF1/3/4)
│   ├── collect-contact-ids.js         # Extract contact IDs for batch send (WF1/3/4)
│   └── merge-fresh-stage.js           # [Placeholder - extract from WF2 when needed]
├── templates/               # Examples and reference materials
│   └── high-performing-examples.md    # Real examples of successful messages
└── README.md                # This file
```

## How This Works

### The n8n Workflow Architecture

SAB has 5 main AI-driven workflows:

1. **WF1: New Lead Daily** (runs 4am daily)
   - Analyzes new leads → Writes messages → Compliance check → Rewrite if needed
   - Uses: Lead Analyst (new), Copywriter (new), Compliance, Rewriter

2. **WF2: Reply Handler** (runs continuously)
   - Classifies inbound replies → Drafts appropriate responses
   - Uses: Reply Classifier, Response Drafter

3. **WF3: Ghosted Lead Reactivation** (weekly)
   - Re-engages leads who have gone silent
   - Uses: Lead Analyst (ghosted), Copywriter (ghosted), Compliance, Rewriter

4. **WF4: Nurture Stream** (daily)
   - Guides engaged leads toward next steps
   - Uses: Lead Analyst (nurture), Copywriter (nurture), Compliance, Rewriter

5. **WF5: Weekly Reporting** (Sundays 10am)
   - Generates insights on campaign performance
   - Uses: Weekly Analyst

### How System Messages Are Deployed

Each AI Agent node in n8n gets a **system message** - the instructions that tell the AI how to behave.

**The Old Way**: Store the entire system message in n8n (monolithic, hard to maintain, version control nightmare)

**The New Way** (this repo):
1. Keep foundations and roles in Git
2. When a change is made, commit to this repo
3. n8n fetches the assembled file via GitHub raw URL
4. Changes propagate immediately across all instances

Example n8n configuration:
```
AI Agent Node: "Copywriter (WF1)"
└─ System Message Source: https://raw.githubusercontent.com/[owner]/sab-ai-skills/main/assembled/wf1-copywriter.md
```

## How to Edit Skills

### Scenario 1: Fix a Natural Typing Issue

If messages are being sent with em-dashes (they shouldn't be):

1. Open `foundations/natural-typing.md`
2. Update the "NO EM-DASHES" rule section
3. Commit: `git commit -m "fix: clarify em-dash rule with examples"`
4. The change applies to ALL roles that use this foundation

### Scenario 2: Add a New Compliance Rule

If legal needs a new compliance rule added:

1. Open `foundations/australian-compliance.md`
2. Add the new rule in the appropriate section (ASIC/SPAM/ACL/NCC)
3. Include: rule code, constraint, test, severity
4. Commit: `git commit -m "compliance: add new ASIC rule XYZ per legal memo"`
5. All Compliance Checker and Rewriter roles use the updated rule immediately

### Scenario 3: Improve Copywriter Tone for Ghosted Leads

If you want to adjust how Copywriter approaches ghosted leads:

1. Open `roles/copywriter-ghosted.md`
2. Update the "Message Strategies" section with new approaches
3. Commit: `git commit -m "improve: ghosted copywriter tone to be softer and more permission-based"`
4. Only WF3 (Ghosted) is affected; WF1 (New Lead) and WF4 (Nurture) unchanged

### Scenario 4: Create a New Messaging Angle

If you want to introduce a new angle beyond CURIOSITY/SOCIAL_PROOF/etc:

1. Add it to `roles/lead-analyst-*.md` under "Messaging Angle Recommendation"
2. Add execution examples to the relevant `roles/copywriter-*.md`
3. Commit: `git commit -m "feature: add OBJECTION_ADDRESSING angle to lead analyst"`
4. Update assembled files (see next section)

## How to Assemble Files

When you change a foundation or role, you need to re-assemble the production files:

```bash
# Manual assembly (if you update foundations/natural-typing.md):
# The "assembled" files are created by combining:
# - All relevant foundations (listed at top of each assembled file)
# - The role-specific content

# For example, assembled/wf1-copywriter.md = 
#   - foundations/natural-typing.md
#   - foundations/sender-name-rules.md
#   - foundations/vehicle-type-handling.md
#   - foundations/sms-segment-awareness.md
#   - foundations/sab-internal-rules.md
#   + roles/copywriter-new-lead.md

# Most assembly can be scripted - see /scripts/assemble.py (when created)
```

**Important**: The assembled files are what get deployed to n8n. If you update a foundation or role, you MUST update the assembled files before committing.

## Compliance and Risk

All assembled files are tagged with:
- Last assembly date
- Which workflow and node it's for
- Source foundations and roles used

### Rollback Process

If a system message causes issues:

1. Identify which assembled file is problematic
2. Review Git history: `git log --oneline assembled/wf1-copywriter.md`
3. Find the last good commit
4. Revert: `git revert [commit-hash]`
5. Test in n8n
6. The change deploys to all instances using that file

## File Maintenance Rules

### Foundations
- **Keep them focused**: One concern per file (e.g., natural-typing.md covers ONLY typing style)
- **Make them reusable**: Write as if they'll be combined with many different roles
- **Version them carefully**: Changes to foundations affect all roles that use them
- **Document thoroughly**: Include examples and edge cases

### Roles
- **Keep them modular**: Each role handles one responsibility (Lead Analyst, Copywriter, Compliance, etc.)
- **Reference foundations**: List required foundations at the top as a comment
- **Don't repeat**: Never copy-paste foundation content into a role file
- **Include output formats**: Each role must specify exactly what it returns (JSON schema)

### Assembled Files
- **These are production code**: Treat them like deployed software
- **Always include headers**: Timestamp, workflow, source files
- **Test before pushing**: Verify the assembled message matches what n8n expects
- **Keep them in sync**: If a foundation or role changes, re-assemble immediately

## Version Control Practices

### Commit Messages

```
# Fixing a bug
git commit -m "fix: remove false urgency language from ghosted copywriter"

# Adding a feature
git commit -m "feature: add timezone awareness to send-time-optimisation"

# Updating compliance
git commit -m "compliance: update SPAM Act rules per legal review"

# Revising a role
git commit -m "improve: make nurture analyst more sensitive to objections"
```

### Branch Strategy

- **main**: Production-ready, deployed to n8n
- **develop**: Testing new features before merging to main
- **feature/**: Individual improvements (e.g., `feature/add-indigenous-sensitivity-rules`)

### Before Pushing to Main

1. Update ALL assembled files that reference changed foundations/roles
2. Review changes in context (how will this affect actual lead engagement?)
3. Test the assembled files in n8n sandbox
4. Get approval from compliance/ops if touching compliance or brand voice

## Testing in n8n

To test a change:

1. Create a branch: `git checkout -b test/my-change`
2. Update the assembled file
3. In n8n, temporarily point one AI Agent to your test file (raw GitHub URL from branch)
4. Send test messages and verify behavior
5. If good, merge to main and update n8n config
6. If not good, adjust, commit, and test again

## Real Examples

See `templates/high-performing-examples.md` for:
- Actual messages that got high response rates
- The messaging angles that worked
- Why they worked (with callback to the roles/foundations)
- Common failure cases and how they were fixed

## FAQ

**Q: How do I change the tone of ALL copywriter messages?**
A: Edit `roles/copywriter-*.md` (there are three: new-lead, ghosted, nurture). Then re-assemble.

**Q: What if n8n still references an old system message?**
A: Check the AI Agent node settings - it should be pointing to the raw GitHub URL of the assembled file on main branch. If it's hardcoded text, it needs updating to use the URL instead.

**Q: Can I test a change without affecting production?**
A: Yes - use a feature branch and test with n8n's "Preview" mode pointing to your branch URL. When ready, merge to main and update n8n to point to main.

**Q: Who maintains this repo?**
A: The person/team responsible for SAB's AI operations, with compliance oversight for any rules changes.

**Q: What if a role needs to use a foundation that doesn't exist?**
A: Create the foundation file first, then create/update the role to reference it. Don't duplicate content.

## Contact & Support

For questions about:
- **Writing skills**: Check the relevant role file (e.g., `roles/copywriter-new-lead.md`)
- **Compliance rules**: See `foundations/australian-compliance.md`
- **Brand voice**: See `roles/copywriter-*.md` and `foundations/sab-internal-rules.md`
- **Deployment**: See "How System Messages Are Deployed" above

---

**Last Updated**: 2026-02-28
**Repository Version**: 1.0 (Initial decomposition from n8n)

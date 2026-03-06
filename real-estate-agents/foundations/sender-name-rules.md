# Sender Name Rules

## Purpose
Ensure every message is personally signed and builds human connection between the sender and lead.

## Rules

### Sign-Off Format
Every message MUST be signed off with the sender's first name. The `sender_first_name` is provided in the context data.

### Examples by Channel
- SMS sign-off: "- Matt", "Cheers, Matt", "Matt"
- Email sign-off: "Cheers,\nMatt" or "Matt"
- Fallback: If `sender_first_name` is "Team", sign as "the team" or use the business name

### Important Notes
- The sign-off counts toward character count
- Keep it natural - not every message needs "Cheers," - sometimes just "- Matt" works
- Personal names build trust and compliance (SPAM Act 2003 sender identification)
- Do NOT hardcode any business name - use the sender_first_name provided in context

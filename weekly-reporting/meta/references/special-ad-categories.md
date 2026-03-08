# Special Ad Categories Reference

Meta's Special Ad Categories (SACs) restrict targeting options and affect how creative must be written. This pipeline must detect SACs before analysis and flag them in output. Never suggest audience restrictions for accounts running in a Special Ad Category.

---

## Credit (Financial Products)

**Applies when:** advertising financial products including loans, insurance, credit cards, mortgages, financial services.

### Targeting restrictions (automatically enforced by Meta)
- Age targeting disabled — must serve all ages 18+
- Gender targeting disabled
- Postcode exclusions limited
- Detailed targeting options restricted

### Accounts in this pipeline with Credit category
| Account | Meta Account ID |
|---------|----------------|
| Strategic Mortgage Brokers | `act_2554789344674358` |
| Dashdot | `act_229691921275637` |

### Creative restrictions
- Cannot use fear-based income claims
- Cannot make specific savings guarantees ("You could save $X")
- Cannot imply guaranteed approval
- Claims must be general and factual

### Pipeline behaviour
When Skill 1 detects a Credit category account, it must:
1. Print `CREDIT CATEGORY ACTIVE` in the analysis output
2. NOT suggest audience narrowing in recommendations
3. Flag in the markdown brief: "⚠️ Credit Special Ad Category — targeting restrictions apply"

---

## Housing

**Applies when:** advertising real estate sales, rentals, home loans, mortgage refinancing, or related housing services.

### Targeting restrictions
- Same restrictions as Credit (age, gender, postcode all restricted)

### Accounts
- Any real estate clients added to this pipeline
- Check account config in `creative_config.py` for `special_category: "housing"` flag

### Creative restrictions
- Cannot make discriminatory statements (explicit or implied) about neighbourhoods
- Cannot use language that implies targeting by race, religion, national origin, family status, or disability
- Fair Housing Act compliance required for US-based accounts

---

## Employment

**Applies when:** advertising job listings, recruitment services, employment agencies, staffing platforms.

### Targeting restrictions
- Demographic targeting (age, gender) restricted
- Cannot exclude people based on protected characteristics

### Creative restrictions
- Cannot imply preference for specific age groups
- Cannot use language that discourages protected-class applicants

---

## Detection in Skill 1

Skill 1 automatically checks for Special Ad Categories before pulling insights:

```python
# Check if account has Special Ad Category active
url = f"{META_BASE}/act_{account_id}/campaigns"
params = {
    "fields": "special_ad_categories",
    "limit": 50,
    "access_token": META_TOKEN,
}
data = _meta_get(url, params)

active_categories = set()
for campaign in data.get("data", []):
    cats = campaign.get("special_ad_categories", [])
    active_categories.update(cats)

if active_categories:
    print(f"  ⚠️  Special Ad Categories detected: {active_categories}")
    # Store in account analysis context
    account_context["special_ad_categories"] = list(active_categories)
```

If `special_ad_categories != []` → the category is flagged in all output for that account.

---

## What This Means for Copy Generation (Skill 2)

When a Special Ad Category is active, Skill 2's GPT-4o prompt is modified to include:

```
COMPLIANCE NOTE: This account has [CREDIT/HOUSING/EMPLOYMENT] Special Ad Category active.
Do not suggest:
  - Specific savings amounts or guarantees
  - Fear-based financial claims
  - Language that could imply demographic targeting
All copy must be factual and general.
```

---

## Summary Table

| Category | Age targeting | Gender targeting | Postcode exclusions | Pipeline flag |
|----------|--------------|-----------------|--------------------|----|
| Credit | ❌ Disabled | ❌ Disabled | ⚠️ Limited | `CREDIT CATEGORY ACTIVE` |
| Housing | ❌ Disabled | ❌ Disabled | ⚠️ Limited | `HOUSING CATEGORY ACTIVE` |
| Employment | ⚠️ Restricted | ⚠️ Restricted | ✅ Allowed | `EMPLOYMENT CATEGORY ACTIVE` |
| None | ✅ Full | ✅ Full | ✅ Full | — |

# Campaign Objectives Reference

How Meta campaign objective types affect the Creative Intelligence Pipeline. Read this before interpreting CPL data or comparing ad performance across campaigns.

---

## Standard Objectives (New API Names)

### `OUTCOME_SALES`
- Optimises for purchase events
- **CPL metric is really CPA-purchase** — this is not a lead metric
- If a client uses `OUTCOME_SALES` to drive form fills: check which action type is being counted in the Insights API
- Confirm pixel fires on the **thank-you page**, not add-to-cart — false attribution is common
- In Skill 1: if action type is `purchase` but funnel is a lead funnel, flag "WARNING: OUTCOME_SALES campaign used for lead funnel — CPL comparison invalid"

### `OUTCOME_LEADS`
- Two sub-modes: **Website leads** (pixel-fired) vs **Instant Forms** (Meta-native)
- **Instant form leads are NOT counted via pixel** — use `lead_component_id` in the Insights API to get them
- Quality varies massively: instant forms typically lower quality than website leads
- Always check the campaign's primary optimisation event before treating leads as equivalent
- In Skill 1: flag if mixing instant form and website lead campaigns in the same funnel comparison

### `OUTCOME_AWARENESS`
- CPM-optimised — **not conversion-optimised**
- Creative winner logic does not apply to awareness campaigns
- Use CPM and reach as metrics, not CPL
- In Skill 1: exclude `OUTCOME_AWARENESS` campaigns from CPL analysis automatically

### `OUTCOME_ENGAGEMENT`
- Optimises for post engagement (likes, comments, shares)
- **Will inflate lead counts with false "page like" actions** — filter these out
- Do not include engagement campaign actions in CPL calculations
- In Skill 1: filter `post_reaction` and `like` action types from conversion count

### `OUTCOME_TRAFFIC`
- Click-optimised
- Higher CTR than `OUTCOME_LEADS` but lower lead quality
- CTR is not a reliable proxy for CPL — do not compare traffic and leads campaigns
- In Skill 1: exclude from CPL benchmark unless specifically requested

### `OUTCOME_APP_PROMOTION`
- Mobile installs
- Not relevant to this pipeline — skip

---

## Advantage+ Shopping Campaigns (ASC)

- **No ad set targeting controls** — Meta chooses audience targeting automatically
- Budget is always at campaign level (CBO is forced — cannot use ABO)
- Cannot run ABO with ASC
- **Creative reporting:** pull results per ad, not per ad set — ad set reporting is meaningless in ASC
- In Skill 1 analysis: pull ad-level insights only for ASC campaigns; ignore adset-level aggregations

---

## ABO vs CBO

### ABO (Ad Set Budget)
- Budget set per ad set
- Equal spend distribution across ad sets = better for testing
- **Recommended for this pipeline's test batches** — ensures all new variants get impressions
- Use ABO when launching new creative batches

### CBO (Campaign Budget)
- Meta distributes budget across ad sets based on predicted performance
- Favours proven ad sets — new creative may be starved of spend
- Good for scaling proven concepts
- Use CBO after a winner is identified

### ⚠️ Never switch ABO → CBO mid-flight
Switching resets the learning phase for all affected ad sets. Always document budget type before analysis.

---

## Learning Phase

Any ad set that has received **fewer than 50 optimisation events in the last 7 days** is in the learning phase.

### Rules (enforced in Skill 1):
- **NEVER pause or edit ad sets in learning phase** — resets learning
- **Never kill an ad in learning phase** — insufficient data to judge
- **Never make budget changes > 20%** on scaling ad sets
- In Skill 1: flag all ads where `conversions_7d < 50` with `is_learning = True`

```python
# Learning phase detection in Skill 1
if conversions_7d < 50:
    ad["is_learning"] = True
    # Exclude from CPL comparisons
    # Exclude from 3x kill rule checks
```

---

## Custom Conversion Events Seen in Client Accounts

| Event | Description | Quality signal |
|-------|-------------|----------------|
| `lead` | Standard lead event | Medium |
| `offsite_conversion.fb_pixel_lead` | Pixel-fired lead | Medium-High |
| `omni_complete_registration` | Registration completion | Medium |
| `contact` | Contact form submission | Lower (often lower intent) |
| `purchase` | Purchase event — sometimes used for B2B "demo booked" | Context-dependent — can be misleading |

**Always check which event is set as the campaign's primary optimisation event** before comparing CPLs across campaigns. Two campaigns with identical CPL but different events are not equivalent.

---

## Mixed Objectives Warning

If an account has `OUTCOME_SALES` AND `OUTCOME_LEADS` campaigns both driving to the same destination URL, CPLs are NOT comparable.

**Skill 1 flags this automatically:**

```
WARNING: Mixed campaign objectives detected — CPL comparisons within funnel may be misleading.
Campaigns: [OUTCOME_LEADS: <campaign_name>] + [OUTCOME_SALES: <campaign_name>]
Recommend: Filter to single objective before ranking.
```

---

## Decision Tree for Skill 1 Analysis

```
Is the campaign OUTCOME_AWARENESS or OUTCOME_TRAFFIC?
  → Exclude from CPL analysis

Is the campaign ASC?
  → Pull ad-level only, not adset-level

Is the ad set in learning phase (conversions_7d < 50)?
  → Mark is_learning = True, exclude from kill flag checks

Are there mixed objectives in this funnel?
  → Flag warning, proceed but label clearly

Does the account have Special Ad Categories?
  → See references/special-ad-categories.md
```

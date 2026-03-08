# Quality Gates Reference

Hard rules that govern when data is included in analysis, when ads are flagged, and when comparisons are valid. These gates are enforced in Skill 1's `run_quality_checks()` function. **Never override these rules without explicit human approval.**

---

## Kill Rules

### 3× Kill Threshold

Flag (but never automatically kill) any ad that meets ALL of the following:

1. CPL > 3× the funnel median CPL
2. Spend ≥ $100 (sufficient data)
3. Not in learning phase (`is_learning = False`)
4. Live for > 7 days

**Output format:**
```
⚠️ 3x KILL FLAG: 'Ad Name Here' CPL $84.20 vs funnel median $24.10
  Spend: $312.40 | Conversions: 3 | Days live: 14
  Recommended action: Pause and review with media buyer.
```

The script flags — it does not pause. A human must review and take action.

### Never Kill These

| Condition | Reason |
|-----------|--------|
| `is_learning = True` (conversions_7d < 50) | Insufficient optimisation data |
| Spend < $50 | Insufficient statistical data |
| Live for < 7 days | Not enough time to ramp |

These ads are excluded from the 3× kill flag check even if CPL is high.

---

## Budget Sufficiency

Meta requires at least **50 optimisation events per 7 days** for an ad set to exit learning phase.

### Minimum budget rule

Valid learning requires: `daily budget ≥ (5 × target CPA) / 7`

If an ad set's daily budget is below this threshold, flag it:

```
⚠️ UNDERFUNDED: Ad set '{adset_name}' budget ${daily_budget}/day
  Required for valid learning: ${required}/day (at ${target_cpa} CPA)
  Result: learning phase will never exit — data is unreliable
```

> Note: actual daily budget requires a separate API call to the ad set endpoint. If unavailable, flag as `TODO: check adset budget`.

---

## Learning Phase Protection

| Rule | Hard limit |
|------|-----------|
| Edits to ad sets in learning phase | Never |
| Budget changes on scaling ad sets | Max 20% per 7 days |
| Pausing ad sets in learning phase | Never |
| Killing ads in learning phase | Never |

Skill 1 marks all ads with `is_learning` boolean. Downstream skills must respect this flag.

---

## Comparison Validity Rules

Only compare ads that meet ALL of the following:

| Criterion | Minimum |
|-----------|---------|
| Same funnel | Same `base_url_contains` destination |
| Same campaign objective | e.g. both `OUTCOME_LEADS` |
| Minimum spend | ≥ $50 |
| Minimum conversions | ≥ 3 |

### Invalid comparisons (auto-flagged)

- Comparing `OUTCOME_LEADS` vs `OUTCOME_SALES` CPLs: ❌ Invalid — different event types
- Comparing ads in learning phase vs exited: ❌ Invalid — exclude learning phase from benchmark
- Comparing ads with spend < $50: ❌ Invalid — insufficient data
- Comparing instant form vs website pixel leads: ❌ Invalid — different lead quality

---

## Quality Check Code (Skill 1)

```python
def run_quality_checks(ads_by_funnel: dict, account_config: dict) -> list:
    """Run quality gate checks on the pulled ad data. Return list of warnings."""
    warnings = []

    for funnel, ads in ads_by_funnel.items():
        for ad in ads:
            spend = ad.get("spend", 0)
            cpl = ad.get("cpl", 999)
            conversions = ad.get("conversions", 0)
            conversions_7d = ad.get("conversions_7d", conversions)  # approximation

            # Learning phase check
            if conversions_7d < 50:
                ad["is_learning"] = True
                warnings.append(
                    f"[{funnel}] Ad '{ad['ad_name']}' may be in learning phase (<50 conversions/7d)"
                )
            else:
                ad["is_learning"] = False

            # Budget sufficiency: flag as TODO if daily budget unavailable
            # (actual daily budget needs a separate API call to ad set endpoint)

        # 3x kill rule check (flag only — never actually kill)
        eligible = [
            a for a in ads
            if a.get("spend", 0) >= 100 and not a.get("is_learning", True)
        ]
        if eligible:
            import statistics
            cpls = [a["cpl"] for a in eligible]
            median_cpl = statistics.median(cpls)
            for ad in eligible:
                if ad.get("cpl", 0) > (3 * median_cpl):
                    warnings.append(
                        f"[{funnel}] ⚠️ 3x KILL FLAG: '{ad['ad_name']}' "
                        f"CPL ${ad['cpl']:.2f} vs median ${median_cpl:.2f}"
                    )

    return warnings
```

---

## Output in Master Brief

All warnings are included in the master Creative Brief markdown:

```markdown
## ⚠️ Quality Gate Warnings

- [labour_calc] Ad 'Xero Hook V3' may be in learning phase (<50 conversions/7d)
- [labour_calc] ⚠️ 3x KILL FLAG: 'Stock Photo V1' CPL $84.20 vs median $24.10
```

Warnings do not block the pipeline — they are informational flags for the media buyer.

---

## Escalation

If any of the following occur, pause the pipeline and notify the media buyer before proceeding:

1. All ads in a funnel are flagged as learning phase
2. Funnel has fewer than 3 qualifying ads (spend ≥ $50, conversions ≥ 3)
3. More than 50% of ads in funnel hit the 3× kill flag
4. Median funnel CPL has increased > 50% week-over-week

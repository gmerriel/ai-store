"""
creative_config.py — Shared config and helpers for the Creative Intelligence Pipeline.

CREDENTIALS
-----------
Read from environment variables. Locally: create weekly-reporting/meta/.env (gitignored).
    META_TOKEN=...
    OPENAI_API_KEY=...
    SUPABASE_URL=...
    SUPABASE_KEY=...

FUNNEL AUTO-DETECTION
---------------------
Funnels are NOT pre-configured per account. Skill 1 pulls all active campaigns,
slugifies the campaign name, and groups ads by that slug. This means ANY client
account works with zero funnel config — just add the account and skip lists.

Skip logic (two layers):
  1. skip_objectives  — ignore campaigns with these Meta objectives entirely
  2. skip_name_contains — ignore campaigns whose name contains any of these strings

Campaign name → funnel slug algorithm:
  1. Strip agency prefix:   "VM: ", "PT: "
  2. Strip geo prefix:      "AU&NZ - ", "USA&CA - ", "AU/NZ - ", "US/CA - " etc.
  3. Strip warm/cold:       "Warm - ", "Cold - "
  4. Strip everything from first technical token: ADV+, ABO, CBO, LAL, Hyros, Tradies...
  5. Strip trailing parentheticals
  6. Slugify remaining string → funnel key

Examples:
  "VM: AU&NZ - Labour Cost Calc ADV+ - Tradies - Hyros - 300"  →  labour_cost_calc
  "VM: USA&CA - AI Assistant PDF - ADV+ - Tradies (Lead)"       →  ai_assistant_pdf
  "PT: AU/NZ - Warm - Profitable Tradie Book - 390"             →  profitable_tradie_book
  "VM: AU&NZ - Free Planning (Form) - CBO - Warm - Hyros Triage Call - 200"  →  free_planning

AU&NZ and USA&CA variants of the same offer slug-match identically, so
creative_id deduplication merges them into one aggregated record per offer.

CONVERSION EVENTS
-----------------
Skill 1 counts the first matching action type from CONVERSION_PRIORITY_ORDER.
Lead campaigns use lead events; sales campaigns use purchase events.
The scoring is relative (creative_cpl vs funnel_avg_cpl), so the metric label
("CPL" vs "CPS") doesn't matter — consistency within each funnel is what counts.

API
---
Meta Graph API: v23.0
Batch endpoint: https://graph.facebook.com/ (POST, no version prefix)
Batch relative_url: must include version, e.g.  v23.0/{ad_id}?fields=...
URL-encode braces: { = %7B, } = %7D, , = %2C
"""

import os
import re
from datetime import datetime

# ─── .env LOADER ─────────────────────────────────────────────────────────────

def _load_dotenv() -> None:
    env_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    try:
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())
    except FileNotFoundError:
        pass

_load_dotenv()

# ─── CREDENTIALS ─────────────────────────────────────────────────────────────

META_TOKEN     = os.environ["META_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
SUPABASE_URL   = os.environ["SUPABASE_URL"]
SUPABASE_KEY   = os.environ["SUPABASE_KEY"]

# ─── META API ─────────────────────────────────────────────────────────────────

META_API_VERSION = "v23.0"
META_BASE        = f"https://graph.facebook.com/{META_API_VERSION}"
META_BATCH_URL   = "https://graph.facebook.com/"   # No version — batch uses relative_url

# ─── CONVERSION EVENT PRIORITY ────────────────────────────────────────────────
# Skill 1 sums the first matching type(s) found in an ad's actions list.
# Order matters: most specific first.

CONVERSION_PRIORITY_ORDER = [
    # Purchases (book sales, ecommerce)
    "offsite_conversion.fb_pixel_purchase",
    "purchase",
    "omni_purchase",
    # Leads (form fills, PDF downloads, calculator submissions)
    "lead",
    "offsite_conversion.fb_pixel_lead",
    "omni_complete_registration",
    # Appointments / calls
    "schedule",
    "contact",
]

# ─── CAMPAIGN SLUG BUILDER ────────────────────────────────────────────────────

# Patterns stripped from campaign names before slugifying.
# Order matters — strip from left first, then right.
_GEO_PREFIXES = re.compile(
    r'^(AU&NZ|AUS&NZ|USA?&CA|AU/NZ|US/CA|NZ|AU|US|CA|AUS)\s*[-–]\s*',
    re.IGNORECASE,
)
_AGENCY_PREFIX = re.compile(r'^(VM:|PT:|VH:)\s*', re.IGNORECASE)
_WARM_COLD     = re.compile(r'^(Warm|Cold)\s*[-–]\s*', re.IGNORECASE)
_TECH_SUFFIX   = re.compile(
    r'\s*[-–]\s*(ADV\+|ABO|CBO|GamePlan|LAL[\d%]+|Hyros|Tradies|'
    r'Lead\b|Leads\b|Form\b|PDF\b|Triage\b|Free Planning\b|AUS\b|NZD\b|USD\b|\d{3,}).*$',
    re.IGNORECASE,
)
# "ADV+" sometimes appears without a preceding dash (space only before it)
# No \b — "+" is not a word char so word boundaries don't work reliably here
_INLINE_TECH   = re.compile(r'\s+ADV\+.*$', re.IGNORECASE)
_TRAILING_PAREN = re.compile(r'\s*\(.*$')


def campaign_name_to_slug(name: str) -> str:
    """
    Convert a Meta campaign name to a short, stable funnel slug.

    Same slug for AU&NZ and USA&CA variants of the same offer — they merge
    via creative_id deduplication in Phase 1A.
    """
    s = name.strip()
    s = _AGENCY_PREFIX.sub("", s).strip()
    s = _GEO_PREFIXES.sub("", s).strip()
    s = _WARM_COLD.sub("", s).strip()
    s = _TECH_SUFFIX.sub("", s).strip()
    s = _INLINE_TECH.sub("", s).strip()   # catch "ADV+" with no dash before it
    s = _TRAILING_PAREN.sub("", s).strip()
    slug = re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
    return slug or "unknown"


# ─── ACCOUNT CONFIGS ─────────────────────────────────────────────────────────
# No 'funnels' key needed — Skill 1 auto-detects from active campaigns.
# Just provide account metadata and what to skip.

ACCOUNTS = {
    "profitable_tradie": {
        "account_id":  "act_559512967808213",
        "client_id":   "c6065265-f986-47e4-b1b2-acd05afc61f0",
        "client_slug": "profitable_tradie",
        "audience": (
            "Australian trades business owners (plumbers, electricians, builders, roofers). "
            "Typically 30-55. Run businesses of 1-15 people. Time-poor. Pride in their trade."
        ),
        "report_dir": os.path.expanduser("~/reports/profitable_tradie/"),
        # Objectives to skip entirely
        "skip_objectives": ["OUTCOME_ENGAGEMENT", "OUTCOME_TRAFFIC"],
        # Campaign name substrings to skip (case-insensitive)
        "skip_name_contains": [
            "retargeting", "podcast", "instagram profile",
            "follower", "event marketing", "non-delivery",
        ],
    },
    # ── ADD NEW ACCOUNTS BELOW ─────────────────────────────────────────────
    # "fitribe": {
    #     "account_id":  "act_947697689468163",
    #     "client_id":   "...",
    #     "client_slug": "fitribe",
    #     "audience":    "...",
    #     "report_dir":  os.path.expanduser("~/reports/fitribe/"),
    #     "skip_objectives":    ["OUTCOME_ENGAGEMENT", "OUTCOME_TRAFFIC"],
    #     "skip_name_contains": ["retargeting", "podcast"],
    # },
}

# ─── HELPERS ──────────────────────────────────────────────────────────────────


def get_week_str(week_start: str) -> str:
    dt = datetime.strptime(week_start, "%Y-%m-%d")
    y, w, _ = dt.isocalendar()
    return f"{y}W{w:02d}"


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def get_supabase_client():
    try:
        from supabase import create_client  # type: ignore
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except ImportError as exc:
        raise ImportError("Run: pip3 install supabase") from exc


def get_openai_client():
    try:
        import openai  # type: ignore
        return openai.OpenAI(api_key=OPENAI_API_KEY)
    except ImportError as exc:
        raise ImportError("Run: pip3 install openai") from exc

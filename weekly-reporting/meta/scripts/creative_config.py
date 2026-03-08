"""
creative_config.py — Shared config and helpers for the Creative Intelligence Pipeline.

CREDENTIALS
-----------
All credentials are read from environment variables.
Locally: create a .env file in weekly-reporting/meta/ (it's gitignored).
Format:
    META_TOKEN=...
    OPENAI_API_KEY=...
    SUPABASE_URL=...
    SUPABASE_KEY=...

CI/cron: set env vars before running: export $(grep -v '^#' .env | xargs)

FUNNEL DETECTION
----------------
Two-stage matching per funnel:
  1. base_url_contains — checked against destination URL in object_story_spec (most accurate)
  2. name_keywords     — checked against ad_name + campaign_name (fallback for any ad where
                         the landing URL is masked or unavailable)

ACTIVE-ONLY RULE
----------------
Skill 1 fetches insights ONLY for ACTIVE ads (effective_status=ACTIVE).
date_preset=maximum gives all-time historical performance for those ads.
Dead / paused / archived campaigns are excluded entirely.

API VERSION
-----------
Meta Graph API: v23.0 (May 2026 — update if deprecated)
Batch API endpoint: https://graph.facebook.com/ (POST, no version prefix)
Batch relative_url: must include version prefix, e.g. v23.0/{ad_id}?fields=...
Fields with curly braces must be URL-encoded: { = %7B, } = %7D, , = %2C
"""

import os
from datetime import datetime

# ─── .env LOADER ─────────────────────────────────────────────────────────────
# Tries to load ../.env relative to this script (weekly-reporting/meta/.env)
# No third-party packages needed.

def _load_dotenv() -> None:
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    env_path = os.path.normpath(env_path)
    try:
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())
    except FileNotFoundError:
        pass  # Rely on env vars already set (CI, cron, etc.)

_load_dotenv()

# ─── CREDENTIALS ─────────────────────────────────────────────────────────────

META_TOKEN     = os.environ["META_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
SUPABASE_URL   = os.environ["SUPABASE_URL"]
SUPABASE_KEY   = os.environ["SUPABASE_KEY"]

# ─── META API ─────────────────────────────────────────────────────────────────

META_API_VERSION = "v23.0"
META_BASE        = f"https://graph.facebook.com/{META_API_VERSION}"
META_BATCH_URL   = "https://graph.facebook.com/"  # No version prefix — batch uses relative_url

# ─── ACCOUNT CONFIGS ─────────────────────────────────────────────────────────

ACCOUNTS = {
    "profitable_tradie": {
        "account_id": "act_559512967808213",
        "client_id":  "c6065265-f986-47e4-b1b2-acd05afc61f0",
        "client_slug": "profitable_tradie",
        "audience": (
            "Australian trades business owners (plumbers, electricians, builders, roofers). "
            "Typically 30-55. Run businesses of 1-15 people. Time-poor. Pride in their trade."
        ),
        "report_dir": os.path.expanduser("~/reports/profitable_tradie/"),
        "funnels": {
            "labour_calc": {
                "base_url_contains": "labour",
                "name_keywords": [
                    "labour", "labor", "real cost of lab", "labour calc", "labor calc",
                ],
                "offer_name": "Real Cost of Labour Calculator",
                "cta": "Use the free calculator below 👇",
            },
            "ai_assistant": {
                "base_url_contains": "chatgpt",
                "name_keywords": [
                    "chatgpt", "ai assistant", "ai for trades", "ai tool", "ai guide",
                ],
                "offer_name": "ChatGPT for Trades Businesses Guide",
                "cta": "Free below 👇",
            },
            "sys_blueprint": {
                "base_url_contains": "system",
                "name_keywords": [
                    "system", "blueprint", "systems blueprint",
                ],
                "offer_name": "Systems Blueprint PDF",
                "cta": "Free PDF below 👇",
            },
            "pricing_calc": {
                "base_url_contains": "pric",
                "name_keywords": [
                    "pricing calc", "price calc", "job pricing", "pricing calculator",
                ],
                "offer_name": "Pricing Calculator",
                "cta": "Free below 👇",
            },
        },
    },
    # ── ADD NEW ACCOUNTS BELOW ────────────────────────────────────────────────
    # "fitribe": {
    #     "account_id": "act_947697689468163",
    #     "client_id": "...",
    #     "client_slug": "fitribe",
    #     "audience": "...",
    #     "report_dir": os.path.expanduser("~/reports/fitribe/"),
    #     "funnels": { ... },
    # },
}

# ─── HELPERS ─────────────────────────────────────────────────────────────────


def get_week_str(week_start: str) -> str:
    """Return ISO week string like '2026W11' for a YYYY-MM-DD date."""
    dt = datetime.strptime(week_start, "%Y-%m-%d")
    y, w, _ = dt.isocalendar()
    return f"{y}W{w:02d}"


def ensure_dir(path: str) -> None:
    """Create directory (and parents) if it doesn't exist."""
    os.makedirs(path, exist_ok=True)


def get_supabase_client():
    """Return an initialised Supabase client."""
    try:
        from supabase import create_client  # type: ignore
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except ImportError as exc:
        raise ImportError("Run: pip3 install supabase") from exc


def get_openai_client():
    """Return an initialised OpenAI client."""
    try:
        import openai  # type: ignore
        return openai.OpenAI(api_key=OPENAI_API_KEY)
    except ImportError as exc:
        raise ImportError("Run: pip3 install openai") from exc

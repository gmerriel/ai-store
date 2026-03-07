"""
creative_config.py — Shared config, constants, and helpers for the Creative Intelligence Pipeline.
"""

import os
from datetime import datetime, timedelta

# ─── SHARED CONSTANTS ────────────────────────────────────────────────────────

# ─── CREDENTIALS (set via environment variables — never hardcode) ─────────────
# Create a .env file (not committed) or export in your shell:
#
#   export META_TOKEN="your_meta_token"
#   export OPENAI_API_KEY="your_openai_key"
#   export SUPABASE_URL="https://yourproject.supabase.co"
#   export SUPABASE_KEY="your_supabase_anon_key"
#
# Or copy .env.example to .env and fill in your values.

META_TOKEN = os.environ.get("META_TOKEN", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://cndxufrgwgedqfvjrone.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
META_API_VERSION = "v21.0"
META_BASE = f"https://graph.facebook.com/{META_API_VERSION}"

# ─── ACCOUNT CONFIGS ─────────────────────────────────────────────────────────

ACCOUNTS = {
    "profitable_tradie": {
        "account_id": "act_559512967808213",
        "client_id": "c6065265-f986-47e4-b1b2-acd05afc61f0",
        "client_slug": "profitable_tradie",
        "audience": (
            "Australian trades business owners (plumbers, electricians, builders, roofers). "
            "Typically 30-55. Run businesses of 1-15 people. Time-poor. Pride in their trade."
        ),
        "report_dir": "/Users/atlas/reports/profitable_tradie/",
        "funnels": {
            "labour_calc": {
                "base_url_contains": "labour",
                "offer_name": "Real Cost of Labour Calculator",
                "cta": "Use the free calculator below 👇",
            },
            "ai_assistant": {
                "base_url_contains": "chatgpt",
                "offer_name": "ChatGPT for Trades Businesses Guide",
                "cta": "Free below 👇",
            },
            "sys_blueprint": {
                "base_url_contains": "system",
                "offer_name": "Systems Blueprint PDF",
                "cta": "Free PDF below 👇",
            },
            "pricing_calc": {
                "base_url_contains": "pric",
                "offer_name": "Pricing Calculator",
                "cta": "Free below 👇",
            },
        },
    }
}

# ─── HELPER FUNCTIONS ─────────────────────────────────────────────────────────


def get_week_str(week_start: str) -> str:
    """
    Convert a YYYY-MM-DD date string to ISO week format like "2026W10".

    Args:
        week_start: Date string in YYYY-MM-DD format.

    Returns:
        String like "2026W10".
    """
    dt = datetime.strptime(week_start, "%Y-%m-%d")
    iso_year, iso_week, _ = dt.isocalendar()
    return f"{iso_year}W{iso_week:02d}"


def ensure_dir(path: str) -> None:
    """
    Create directory (and all parents) if it does not already exist.

    Args:
        path: Directory path to create.
    """
    os.makedirs(path, exist_ok=True)


def get_supabase_client():
    """
    Initialise and return a Supabase client.

    Returns:
        supabase.Client instance.
    """
    try:
        from supabase import create_client, Client  # type: ignore
        client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return client
    except ImportError as exc:
        raise ImportError(
            "supabase package not installed. Run: pip install supabase"
        ) from exc


def get_openai_client():
    """
    Initialise and return an OpenAI client.

    Returns:
        openai.OpenAI instance.
    """
    try:
        import openai  # type: ignore
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        return client
    except ImportError as exc:
        raise ImportError(
            "openai package not installed. Run: pip install openai"
        ) from exc

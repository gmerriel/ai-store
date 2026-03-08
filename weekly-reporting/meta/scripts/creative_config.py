"""
creative_config.py — Shared config and helpers for the Creative Intelligence Pipeline.

Funnel detection uses TWO methods per funnel:
  1. base_url_contains — matches destination URL (direct links)
  2. name_keywords     — matches ad_name + campaign_name (fallback for fb.me redirect ads)

Credentials: set env vars before running: export $(cat .env | xargs)
"""
import os
from datetime import datetime

META_TOKEN      = os.environ["META_TOKEN"]
OPENAI_API_KEY  = os.environ["OPENAI_API_KEY"]
SUPABASE_URL    = os.environ["SUPABASE_URL"]
SUPABASE_KEY    = os.environ["SUPABASE_KEY"]

META_API_VERSION = "v23.0"
META_BASE = f"https://graph.facebook.com/{META_API_VERSION}"

ACCOUNTS = {
    "profitable_tradie": {
        "account_id": "act_559512967808213",
        "client_id":  "c6065265-f986-47e4-b1b2-acd05afc61f0",
        "client_slug": "profitable_tradie",
        "audience": (
            "Australian trades business owners (plumbers, electricians, builders, roofers). "
            "Typically 30-55. Run businesses of 1-15 people. Time-poor. Pride in their trade."
        ),
        "report_dir": "/reports/profitable_tradie/",
        "funnels": {
            "labour_calc": {
                "base_url_contains": "labour",
                "name_keywords": ["labour", "labor", "real cost of lab", "labour calc", "labor calc"],
                "offer_name": "Real Cost of Labour Calculator",
                "cta": "Use the free calculator below 👇",
            },
            "ai_assistant": {
                "base_url_contains": "chatgpt",
                "name_keywords": ["chatgpt", "ai assistant", "ai for trades", "ai tool", "ai guide"],
                "offer_name": "ChatGPT for Trades Businesses Guide",
                "cta": "Free below 👇",
            },
            "sys_blueprint": {
                "base_url_contains": "system",
                "name_keywords": ["system", "blueprint", "systems blueprint"],
                "offer_name": "Systems Blueprint PDF",
                "cta": "Free PDF below 👇",
            },
            "pricing_calc": {
                "base_url_contains": "pric",
                "name_keywords": ["pricing calc", "price calc", "job pricing", "pricing calculator"],
                "offer_name": "Pricing Calculator",
                "cta": "Free below 👇",
            },
        },
    },
}

def get_week_str(week_start: str) -> str:
    dt = datetime.strptime(week_start, "%Y-%m-%d")
    y, w, _ = dt.isocalendar()
    return f"{y}W{w:02d}"

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def get_supabase_client():
    from supabase import create_client, Client  # type: ignore
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_openai_client():
    import openai  # type: ignore
    return openai.OpenAI(api_key=OPENAI_API_KEY)

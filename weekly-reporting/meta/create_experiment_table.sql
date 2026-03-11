-- ─── Creative Experiment Tracker ─────────────────────────────────────────────
-- Tracks every hook/angle/format tested across all accounts and funnels.
-- Auto-populated by Skill 2 when concepts are generated.
-- Updated manually (or by Atlas) with outcomes after each weekly cycle.
-- Fed back into Skill 2 so GPT-4o never suggests a dead angle twice.

CREATE TABLE IF NOT EXISTS ad_experiments (
    -- Identity
    id              TEXT PRIMARY KEY,                    -- UUID
    account_id      TEXT NOT NULL,                       -- act_xxx
    account_slug    TEXT NOT NULL,                       -- profitable_tradie
    funnel_name     TEXT NOT NULL,                       -- labour_cost_calc

    -- What was tested
    week_launched   TEXT NOT NULL,                       -- YYYY-MM-DD
    concept_id      TEXT,                                -- FK to ad_concepts
    concept_name    TEXT,                                -- human-readable concept name
    hook_index      INTEGER,                             -- 1-5
    hook_type       TEXT,                                -- continuer | explorer
    hook_text       TEXT,                                -- verbatim hook copy
    angle_type      TEXT,                                -- pain | proof | curiosity | mechanism | story | comparison | specific_numbers | pattern_interrupt
    image_format    TEXT,                                -- on-location-photo | whiteboard-scene | etc (if applicable)
    hypothesis      TEXT,                                -- auto-generated 1-liner: "Does [angle] hook outperform avg for [funnel]?"

    -- Outcome (updated after results come in)
    status          TEXT NOT NULL DEFAULT 'ACTIVE',      -- ACTIVE | WINNER | INCONCLUSIVE | KILLED | NOT_LAUNCHED
    week_closed     TEXT,                                -- YYYY-MM-DD when result was recorded
    outcome_cpl     DECIMAL(10,2),                       -- CPL at close (NULL if not launched)
    outcome_spend   DECIMAL(10,2),                       -- spend during test period
    vs_funnel_avg   TEXT,                                -- "0.8x avg" | "1.6x avg" | null
    lesson          TEXT,                                -- 1-2 sentence takeaway for future briefs

    -- Metadata
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for the common query patterns in Skill 2
CREATE INDEX IF NOT EXISTS idx_experiments_funnel  ON ad_experiments(account_slug, funnel_name);
CREATE INDEX IF NOT EXISTS idx_experiments_status  ON ad_experiments(status);
CREATE INDEX IF NOT EXISTS idx_experiments_week    ON ad_experiments(week_launched);
CREATE INDEX IF NOT EXISTS idx_experiments_angle   ON ad_experiments(account_slug, funnel_name, angle_type, status);

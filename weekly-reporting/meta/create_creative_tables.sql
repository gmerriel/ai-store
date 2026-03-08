-- Creative Intelligence Pipeline — Supabase Tables
-- Run this in: supabase.com → your project → SQL Editor → New query → Run
-- Schema version: 2 (patched 2026-03-08 — added missing columns)

-- Table 1: Ad Copy Winners (from Skill 1A)
CREATE TABLE IF NOT EXISTS ad_copy_winners (
    winner_id       TEXT PRIMARY KEY,
    account_id      TEXT NOT NULL,
    funnel_name     TEXT,
    week_start      DATE NOT NULL,
    ad_id           TEXT NOT NULL,
    ad_name         TEXT,
    asset_type      TEXT,           -- 'image' or 'video'
    cpl             NUMERIC(10,2),
    spend           NUMERIC(10,2),
    conversions     INTEGER,
    headline        TEXT,
    body_copy       TEXT,
    rank            SMALLINT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Table 2: Video Transcriptions (from Skill 1B)
CREATE TABLE IF NOT EXISTS ad_video_transcriptions (
    transcription_id    TEXT PRIMARY KEY,
    ad_id               TEXT NOT NULL,
    account_id          TEXT NOT NULL,
    funnel_name         TEXT,
    week_start          DATE NOT NULL,
    cpl                 NUMERIC(10,2),
    spend               NUMERIC(10,2),
    conversions         INTEGER,
    rank                SMALLINT,
    hook_text           TEXT,
    body_text           TEXT,
    cta_text            TEXT,
    full_transcript     TEXT NOT NULL,
    hook_first_10       TEXT,
    word_count          INTEGER,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Table 3: Image Winners (from Skill 1C)
CREATE TABLE IF NOT EXISTS ad_image_winners (
    image_winner_id     TEXT PRIMARY KEY,
    ad_id               TEXT NOT NULL,
    account_id          TEXT NOT NULL,
    funnel_name         TEXT,
    week_start          DATE NOT NULL,
    cpl                 NUMERIC(10,2),
    spend               NUMERIC(10,2),
    conversions         INTEGER,
    rank                SMALLINT,
    local_file_path     TEXT,
    image_format        TEXT,
    text_on_image       TEXT,
    setting             TEXT,
    props               TEXT,
    person_description  TEXT,
    colour_palette      TEXT,
    authenticity_signals TEXT,
    core_visual_claim   TEXT,
    full_analysis       TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Table 4: Ad Concepts (from Skill 2)
CREATE TABLE IF NOT EXISTS ad_concepts (
    concept_id      TEXT PRIMARY KEY,
    account_id      TEXT NOT NULL,
    client_slug     TEXT,
    funnel_name     TEXT,
    week_start      DATE NOT NULL,
    concept_num     TEXT,
    concept_name    TEXT,
    inspired_by     TEXT,
    headline        TEXT,
    body_a          TEXT,
    body_b          TEXT,
    hooks_a         JSONB,
    hooks_b         JSONB,
    source_refs     JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Table 5: Ad Images (from Skill 3)
CREATE TABLE IF NOT EXISTS ad_images (
    image_id        TEXT PRIMARY KEY,
    account_id      TEXT,
    funnel_name     TEXT,
    week_start      DATE,
    concept_id      TEXT REFERENCES ad_concepts(concept_id),
    body_ref        CHAR(1),
    hook_index      SMALLINT,
    hook_type       TEXT,
    image_option    CHAR(1),
    paired_hook_text TEXT,
    json_prompt     TEXT,
    image_format    TEXT,
    image_url       TEXT,
    model_used      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Table 6: Ad Video Scripts (from Skill 4)
CREATE TABLE IF NOT EXISTS ad_video_scripts (
    script_id           TEXT PRIMARY KEY,
    account_id          TEXT,
    funnel_name         TEXT,
    week_start          DATE,
    concept_id          TEXT REFERENCES ad_concepts(concept_id),
    body_ref            CHAR(1),
    hook_index          SMALLINT,
    hook_type           TEXT,
    hook_text           TEXT,
    location            TEXT,
    prop                TEXT,
    action              TEXT,
    action_valid        BOOLEAN DEFAULT true,
    action_warning      TEXT,
    directors_note      TEXT,
    full_script         TEXT,
    estimated_seconds   SMALLINT,
    energy              TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS (Row Level Security) — open for anon reads/writes for now
ALTER TABLE ad_copy_winners ENABLE ROW LEVEL SECURITY;
ALTER TABLE ad_video_transcriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ad_image_winners ENABLE ROW LEVEL SECURITY;
ALTER TABLE ad_concepts ENABLE ROW LEVEL SECURITY;
ALTER TABLE ad_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE ad_video_scripts ENABLE ROW LEVEL SECURITY;

-- Allow anon key full access (adjust later to lock down)
CREATE POLICY "anon_all" ON ad_copy_winners FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "anon_all" ON ad_video_transcriptions FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "anon_all" ON ad_image_winners FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "anon_all" ON ad_concepts FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "anon_all" ON ad_images FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "anon_all" ON ad_video_scripts FOR ALL TO anon USING (true) WITH CHECK (true);

SELECT 'Tables created successfully' AS status;

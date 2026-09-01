-- Karen Database Schema
-- Run this in Supabase SQL editor
-- No raw conversation text is stored here — transcripts stay in IndexedDB

-- ── Users ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_hash       TEXT PRIMARY KEY,       -- HMAC-SHA256 of email, never raw email
    password_hash   TEXT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Sessions ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sessions (
    session_id      TEXT PRIMARY KEY,
    user_hash       TEXT NOT NULL REFERENCES users(user_hash) ON DELETE CASCADE,
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    ended_at        TIMESTAMPTZ,
    topic           TEXT,                   -- e.g. "work stress"
    final_severity  TEXT DEFAULT 'low',     -- low | moderate | high | crisis
    turn_count      INT DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_hash);

-- ── Session Turns (emotion arc, no text) ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS session_turns (
    id              BIGSERIAL PRIMARY KEY,
    session_id      TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    user_hash       TEXT NOT NULL,
    dominant_emotion TEXT,                  -- joy | sadness | anger | fear | disgust | surprise
    severity        TEXT,                   -- low | moderate | high | crisis
    severity_score  FLOAT,
    topic           TEXT,                   -- only on first turn
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_turns_session ON session_turns(session_id);

-- ── ML Signals (anonymised, opt-in for training) ──────────────────────────────
CREATE TABLE IF NOT EXISTS ml_signals (
    id              BIGSERIAL PRIMARY KEY,
    emotion         TEXT,
    severity        TEXT,
    topic           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
    -- No user_hash here — fully anonymised
);

-- ── Row Level Security ────────────────────────────────────────────────────────
-- Backend uses service role key (bypasses RLS)
-- These policies protect data if anon key is ever used accidentally

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_turns ENABLE ROW LEVEL SECURITY;

-- Only service role can access (backend enforces auth)
CREATE POLICY "service_only" ON users USING (false);
CREATE POLICY "service_only" ON sessions USING (false);
CREATE POLICY "service_only" ON session_turns USING (false);

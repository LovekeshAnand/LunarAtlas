-- ============================================================================
-- LunarAtlas API Key & Usage Monitoring Schema Migration
-- Run once against the LunarAtlas PostgreSQL database.
-- ============================================================================

-- 1) Add role column to app_users (if not present)
ALTER TABLE app_users ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'researcher';

-- 2) API Key storage
CREATE TABLE IF NOT EXISTS api_keys (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    key_hash    VARCHAR(64) NOT NULL UNIQUE,   -- SHA-256 hex digest (never store plaintext)
    key_prefix  VARCHAR(12) NOT NULL,           -- First 8 chars for display ("la_7f3a...")
    label       VARCHAR(100) DEFAULT 'Default',
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    last_used   TIMESTAMPTZ,
    expires_at  TIMESTAMPTZ                     -- NULL = never expires
);

-- 3) API Usage monitoring log
CREATE TABLE IF NOT EXISTS api_usage_log (
    id              BIGSERIAL PRIMARY KEY,
    api_key_id      INTEGER REFERENCES api_keys(id) ON DELETE SET NULL,
    user_id         INTEGER REFERENCES app_users(id) ON DELETE SET NULL,
    endpoint        VARCHAR(255) NOT NULL,
    method          VARCHAR(10) DEFAULT 'GET',
    status_code     INTEGER,
    response_time_ms FLOAT,
    request_params  JSONB,
    response_bytes  INTEGER,
    ip_address      VARCHAR(45),
    user_agent      VARCHAR(512),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_user ON api_usage_log(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_key  ON api_usage_log(api_key_id);
CREATE INDEX IF NOT EXISTS idx_usage_time ON api_usage_log(created_at);

-- Migration: Create gim_identities table for GIM ID authentication
-- Description: Stores GIM IDs (pre-shared credentials) with rate limiting support

CREATE TABLE IF NOT EXISTS gim_identities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gim_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'revoked')),

    -- Per-operation rate limits (search and get_fix_bundle are limited)
    daily_search_limit INT DEFAULT 100,
    daily_search_used INT DEFAULT 0,
    daily_reset_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '24 hours',

    -- Lifetime stats
    total_searches INT DEFAULT 0,
    total_submissions INT DEFAULT 0,
    total_confirmations INT DEFAULT 0,
    total_reports INT DEFAULT 0,

    -- Optional metadata
    description TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Index for fast GIM ID lookups
CREATE INDEX IF NOT EXISTS idx_gim_identities_gim_id ON gim_identities(gim_id);

-- Index for status filtering
CREATE INDEX IF NOT EXISTS idx_gim_identities_status ON gim_identities(status);

-- Function to reset daily rate limits (call via cron or trigger)
CREATE OR REPLACE FUNCTION reset_daily_rate_limits()
RETURNS void AS $$
BEGIN
    UPDATE gim_identities
    SET daily_search_used = 0,
        daily_reset_at = NOW() + INTERVAL '24 hours'
    WHERE daily_reset_at <= NOW();
END;
$$ LANGUAGE plpgsql;

-- RLS policies (enable row level security)
ALTER TABLE gim_identities ENABLE ROW LEVEL SECURITY;

-- Allow service role full access
CREATE POLICY "Service role has full access" ON gim_identities
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Allow anon role to read active identities (for validation)
CREATE POLICY "Anon can read active identities" ON gim_identities
    FOR SELECT
    TO anon
    USING (status = 'active');

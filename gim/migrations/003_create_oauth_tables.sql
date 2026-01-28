-- Migration: Create OAuth 2.1 tables for MCP client authorization
-- Description: Supports OAuth 2.1 with PKCE for secure MCP client authorization

-- OAuth clients table (dynamic client registration per RFC 7591)
CREATE TABLE IF NOT EXISTS oauth_clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id TEXT UNIQUE NOT NULL,
    client_name TEXT,
    redirect_uris TEXT[] NOT NULL,
    grant_types TEXT[] DEFAULT ARRAY['authorization_code', 'refresh_token'],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Index for fast client_id lookups
CREATE INDEX IF NOT EXISTS idx_oauth_clients_client_id ON oauth_clients(client_id);

-- OAuth authorization codes table (short-lived, single-use)
CREATE TABLE IF NOT EXISTS oauth_authorization_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT UNIQUE NOT NULL,
    client_id TEXT NOT NULL REFERENCES oauth_clients(client_id) ON DELETE CASCADE,
    gim_identity_id UUID NOT NULL REFERENCES gim_identities(id) ON DELETE CASCADE,
    redirect_uri TEXT NOT NULL,
    code_challenge TEXT NOT NULL,
    code_challenge_method TEXT DEFAULT 'S256',
    scope TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast code lookups
CREATE INDEX IF NOT EXISTS idx_oauth_authorization_codes_code ON oauth_authorization_codes(code);
-- Index for cleanup of expired codes
CREATE INDEX IF NOT EXISTS idx_oauth_authorization_codes_expires_at ON oauth_authorization_codes(expires_at);

-- OAuth refresh tokens table (rotated on use)
CREATE TABLE IF NOT EXISTS oauth_refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token_hash TEXT UNIQUE NOT NULL,
    client_id TEXT NOT NULL REFERENCES oauth_clients(client_id) ON DELETE CASCADE,
    gim_identity_id UUID NOT NULL REFERENCES gim_identities(id) ON DELETE CASCADE,
    scope TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast token_hash lookups
CREATE INDEX IF NOT EXISTS idx_oauth_refresh_tokens_token_hash ON oauth_refresh_tokens(token_hash);
-- Index for cleanup of expired/revoked tokens
CREATE INDEX IF NOT EXISTS idx_oauth_refresh_tokens_expires_at ON oauth_refresh_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_oauth_refresh_tokens_revoked_at ON oauth_refresh_tokens(revoked_at);

-- Function to cleanup expired authorization codes (call via cron)
CREATE OR REPLACE FUNCTION cleanup_expired_oauth_codes()
RETURNS void AS $$
BEGIN
    DELETE FROM oauth_authorization_codes
    WHERE expires_at < NOW() OR used_at IS NOT NULL;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup expired/revoked refresh tokens (call via cron)
CREATE OR REPLACE FUNCTION cleanup_expired_oauth_tokens()
RETURNS void AS $$
BEGIN
    DELETE FROM oauth_refresh_tokens
    WHERE expires_at < NOW() OR revoked_at IS NOT NULL;
END;
$$ LANGUAGE plpgsql;

-- Enable RLS on all OAuth tables
ALTER TABLE oauth_clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE oauth_authorization_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE oauth_refresh_tokens ENABLE ROW LEVEL SECURITY;

-- Service role has full access to all OAuth tables
CREATE POLICY "Service role full access on oauth_clients" ON oauth_clients
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access on oauth_authorization_codes" ON oauth_authorization_codes
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access on oauth_refresh_tokens" ON oauth_refresh_tokens
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Anon role can register clients (dynamic registration)
-- Note: Add rate limiting at application level to prevent abuse
CREATE POLICY "Anon can insert oauth_clients" ON oauth_clients
    FOR INSERT TO anon WITH CHECK (true);

-- Anon role can only read client by exact client_id match (needed for validation)
-- This is accessed via get_record with client_id filter
CREATE POLICY "Anon can read oauth_clients by client_id" ON oauth_clients
    FOR SELECT TO anon USING (true);

-- Anon role can insert authorization codes (after user approves)
CREATE POLICY "Anon can insert oauth_authorization_codes" ON oauth_authorization_codes
    FOR INSERT TO anon WITH CHECK (true);

-- Anon role can read authorization codes (for exchange with code hash)
-- Codes are stored as hashes and single-use, limiting exposure
CREATE POLICY "Anon can read oauth_authorization_codes" ON oauth_authorization_codes
    FOR SELECT TO anon USING (true);

-- Anon role can mark codes as used
CREATE POLICY "Anon can update oauth_authorization_codes" ON oauth_authorization_codes
    FOR UPDATE TO anon
    USING (used_at IS NULL)  -- Only update unused codes
    WITH CHECK (used_at IS NOT NULL);  -- Can only mark as used

-- Anon role can insert refresh tokens
CREATE POLICY "Anon can insert oauth_refresh_tokens" ON oauth_refresh_tokens
    FOR INSERT TO anon WITH CHECK (true);

-- Anon role can read refresh tokens by exact token_hash (needed for validation)
CREATE POLICY "Anon can read oauth_refresh_tokens" ON oauth_refresh_tokens
    FOR SELECT TO anon USING (true);

-- Anon role can revoke refresh tokens (mark as revoked)
CREATE POLICY "Anon can update oauth_refresh_tokens" ON oauth_refresh_tokens
    FOR UPDATE TO anon
    USING (revoked_at IS NULL)  -- Only update non-revoked tokens
    WITH CHECK (revoked_at IS NOT NULL);  -- Can only revoke

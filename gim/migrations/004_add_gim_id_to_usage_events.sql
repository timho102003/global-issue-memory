-- Migration: Add gim_id column to usage_events
-- Purpose: Track which GIM user generated each usage event,
--          enabling per-user profile stats on /dashboard/profile.

ALTER TABLE usage_events ADD COLUMN IF NOT EXISTS gim_id UUID;

-- Index for filtering events by gim_id (profile stats page)
CREATE INDEX IF NOT EXISTS idx_usage_events_gim_id
    ON usage_events (gim_id);

-- Composite index for profile stats queries that filter by gim_id + event_type
CREATE INDEX IF NOT EXISTS idx_usage_events_gim_id_event_type
    ON usage_events (gim_id, event_type);

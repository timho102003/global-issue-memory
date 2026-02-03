-- Migration 006: Add last_revisited_at column to crawler_state
-- Supports revisiting dropped issues to check if they've been resolved on GitHub.

-- Add last_revisited_at column for tracking when dropped issues were last checked
ALTER TABLE crawler_state ADD COLUMN IF NOT EXISTS last_revisited_at TIMESTAMPTZ;

-- Add revisit_count to track how many times an issue has been revisited (optional future use)
ALTER TABLE crawler_state ADD COLUMN IF NOT EXISTS revisit_count INT DEFAULT 0;

-- Create index for efficiently querying dropped issues due for revisit
-- This index covers the common query pattern:
--   status = 'DROPPED' AND (
--     (last_revisited_at IS NULL AND updated_at < threshold) OR
--     (last_revisited_at < threshold)
--   )
CREATE INDEX IF NOT EXISTS idx_crawler_state_dropped_revisit
    ON crawler_state(status, last_revisited_at, updated_at)
    WHERE status = 'DROPPED';

-- Comment explaining the revisit logic:
-- - Dropped issues are revisited after 5+ days
-- - First revisit: last_revisited_at IS NULL, use updated_at as baseline
-- - Subsequent revisits: use last_revisited_at as baseline
-- - On revisit: re-fetch from GitHub, re-apply filters
--   - If passes: reset to PENDING for full pipeline reprocessing
--   - If still fails: update last_revisited_at to now

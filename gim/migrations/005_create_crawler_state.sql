-- Migration 005: Add crawler state table and source column to master_issues
-- Supports the GitHub issue crawler for populating GIM from resolved bugs.

-- Part A: Add source column to master_issues
ALTER TABLE master_issues ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'mcp_tool';
CREATE INDEX IF NOT EXISTS idx_master_issues_source ON master_issues(source);

-- Part B: Create crawler_state table
CREATE TABLE IF NOT EXISTS crawler_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- GitHub issue identity
    repo TEXT NOT NULL,
    issue_number INT NOT NULL,
    github_issue_id BIGINT,

    -- Pipeline status
    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'FETCHED', 'EXTRACTED', 'SUBMITTED', 'DROPPED', 'ERROR')),
    drop_reason TEXT,

    -- GitHub metadata
    closed_at TIMESTAMPTZ,
    state_reason TEXT,
    has_merged_pr BOOLEAN DEFAULT FALSE,
    pr_number INT,
    issue_title TEXT,
    issue_labels JSONB DEFAULT '[]',

    -- Raw fetched data
    raw_issue_body TEXT,
    raw_comments JSONB DEFAULT '[]',
    raw_pr_body TEXT,
    raw_pr_diff_summary TEXT,

    -- LLM extraction results
    extracted_error TEXT,
    extracted_root_cause TEXT,
    extracted_fix_summary TEXT,
    extracted_fix_steps JSONB DEFAULT '[]',
    extracted_language TEXT,
    extracted_framework TEXT,
    extraction_confidence FLOAT,

    -- Quality scoring
    quality_score FLOAT,

    -- GIM linkage
    gim_issue_id UUID,

    -- Error handling
    last_error TEXT,
    retry_count INT DEFAULT 0,

    -- Audit timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Deduplication
    UNIQUE(repo, issue_number)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_crawler_state_status ON crawler_state(status);
CREATE INDEX IF NOT EXISTS idx_crawler_state_repo ON crawler_state(repo);
CREATE INDEX IF NOT EXISTS idx_crawler_state_quality_score ON crawler_state(quality_score);
CREATE INDEX IF NOT EXISTS idx_crawler_state_created_at ON crawler_state(created_at);

-- Enable RLS
ALTER TABLE crawler_state ENABLE ROW LEVEL SECURITY;

-- Service role has full access
CREATE POLICY "Service role full access on crawler_state"
    ON crawler_state
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Anon can read crawler state stats (status/repo/counts only)
-- No anon read policy on full table to avoid exposing raw data and errors.
-- Use service_role for all programmatic access.

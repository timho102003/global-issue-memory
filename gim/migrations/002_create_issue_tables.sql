-- Create master_issues table
CREATE TABLE IF NOT EXISTS master_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_error TEXT NOT NULL,
    sanitized_context TEXT,
    sanitized_mre TEXT,
    root_cause TEXT NOT NULL,
    root_cause_category TEXT,
    model_provider TEXT,
    language TEXT,
    framework TEXT,
    verification_count INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_verified_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Create child_issues table
CREATE TABLE IF NOT EXISTS child_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    master_issue_id UUID REFERENCES master_issues(id) ON DELETE CASCADE,
    original_error TEXT NOT NULL,
    original_context TEXT,
    code_snippet TEXT,
    model TEXT,
    provider TEXT,
    language TEXT,
    framework TEXT,
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Create fix_bundles table
CREATE TABLE IF NOT EXISTS fix_bundles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_id UUID NOT NULL,
    summary TEXT NOT NULL,
    fix_steps JSONB DEFAULT '[]',
    code_changes JSONB DEFAULT '[]',
    environment_actions JSONB DEFAULT '[]',
    verification_steps JSONB DEFAULT '[]',
    confidence_score FLOAT DEFAULT 0.0,
    verification_count INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_confirmed_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Create usage_events table
CREATE TABLE IF NOT EXISTS usage_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,
    issue_id UUID,
    model TEXT,
    provider TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_master_issues_root_cause_category ON master_issues(root_cause_category);
CREATE INDEX IF NOT EXISTS idx_master_issues_language ON master_issues(language);
CREATE INDEX IF NOT EXISTS idx_master_issues_framework ON master_issues(framework);
CREATE INDEX IF NOT EXISTS idx_child_issues_master_issue_id ON child_issues(master_issue_id);
CREATE INDEX IF NOT EXISTS idx_fix_bundles_issue_id ON fix_bundles(issue_id);
CREATE INDEX IF NOT EXISTS idx_usage_events_event_type ON usage_events(event_type);
CREATE INDEX IF NOT EXISTS idx_usage_events_created_at ON usage_events(created_at);

-- Enable RLS
ALTER TABLE master_issues ENABLE ROW LEVEL SECURITY;
ALTER TABLE child_issues ENABLE ROW LEVEL SECURITY;
ALTER TABLE fix_bundles ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_events ENABLE ROW LEVEL SECURITY;

-- Service role has full access
CREATE POLICY "Service role full access on master_issues" ON master_issues
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access on child_issues" ON child_issues
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access on fix_bundles" ON fix_bundles
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access on usage_events" ON usage_events
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Anon can read issues
CREATE POLICY "Anon can read master_issues" ON master_issues
    FOR SELECT TO anon USING (true);
CREATE POLICY "Anon can read fix_bundles" ON fix_bundles
    FOR SELECT TO anon USING (true);

-- Anon can insert issues and events (submissions are anonymous)
CREATE POLICY "Anon can insert master_issues" ON master_issues
    FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "Anon can insert child_issues" ON child_issues
    FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "Anon can insert fix_bundles" ON fix_bundles
    FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "Anon can insert usage_events" ON usage_events
    FOR INSERT TO anon WITH CHECK (true);

-- Anon can update verification counts
CREATE POLICY "Anon can update master_issues verification" ON master_issues
    FOR UPDATE TO anon USING (true) WITH CHECK (true);
CREATE POLICY "Anon can update fix_bundles verification" ON fix_bundles
    FOR UPDATE TO anon USING (true) WITH CHECK (true);

# GIM Database Schema

This document describes the database tables and schema used by GIM.

## Overview

GIM uses a hybrid storage approach:

- **Supabase (PostgreSQL)**: Stores metadata, authentication, and structured data
- **Qdrant**: Stores vector embeddings for semantic search

## Supabase Tables

### gim_identities

Stores GIM IDs (authentication credentials) with rate limiting and usage tracking.

**Table Schema**:

```sql
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
```

**Indexes**:

```sql
CREATE INDEX IF NOT EXISTS idx_gim_identities_gim_id ON gim_identities(gim_id);
CREATE INDEX IF NOT EXISTS idx_gim_identities_status ON gim_identities(status);
```

**Row Level Security (RLS)**:

```sql
-- Enable RLS
ALTER TABLE gim_identities ENABLE ROW LEVEL SECURITY;

-- Service role has full access
CREATE POLICY "Service role has full access" ON gim_identities
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Anon role can read active identities (for validation)
CREATE POLICY "Anon can read active identities" ON gim_identities
    FOR SELECT
    TO anon
    USING (status = 'active');
```

**Fields Explained**:

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Internal database ID (primary key) |
| `gim_id` | UUID | Public GIM ID used for authentication (unique) |
| `created_at` | TIMESTAMPTZ | When the identity was created |
| `last_used_at` | TIMESTAMPTZ | Last time the identity was used for authentication |
| `status` | TEXT | Status: 'active', 'suspended', or 'revoked' |
| `daily_search_limit` | INT | Maximum search operations per day (default: 100) |
| `daily_search_used` | INT | Number of searches used today |
| `daily_reset_at` | TIMESTAMPTZ | When the daily counters reset (next midnight UTC) |
| `total_searches` | INT | Lifetime count of search operations |
| `total_submissions` | INT | Lifetime count of issue submissions |
| `total_confirmations` | INT | Lifetime count of fix confirmations |
| `total_reports` | INT | Lifetime count of usage reports |
| `description` | TEXT | Optional description of what this GIM ID is for |
| `metadata` | JSONB | Additional metadata (free-form JSON) |

**Status Values**:

- `active`: GIM ID is valid and can be used
- `suspended`: Temporarily disabled (can be reactivated)
- `revoked`: Permanently disabled (cannot be reactivated)

### Rate Limit Reset Function

A stored procedure to reset daily rate limits:

```sql
CREATE OR REPLACE FUNCTION reset_daily_rate_limits()
RETURNS void AS $$
BEGIN
    UPDATE gim_identities
    SET daily_search_used = 0,
        daily_reset_at = NOW() + INTERVAL '24 hours'
    WHERE daily_reset_at <= NOW();
END;
$$ LANGUAGE plpgsql;
```

**Note**: This function can be called via cron job or trigger. The GIM server also checks and resets limits automatically when needed.

## Qdrant Collections

### gim_issues

Vector collection storing sanitized issues with embeddings for semantic search.

**Collection Configuration**:

```python
{
    "vectors": {
        "size": 3072,  # gemini-embedding-001 dimension
        "distance": "Cosine"
    },



   "quantization_config": {
           "scalar": {
            "type": "int8",
            "quantile": 0.99,
            "always_ram": True
        }
    }
}
```

**Quantization Features**:
- **INT8 scalar quantization**: Reduces memory usage by 4x while maintaining search quality
- **always_ram=True**: Keeps quantized vectors in RAM for fast search (no disk I/O)
- **Re-scoring enabled**: Uses `oversampling=2.0` to improve precision by re-ranking with full vectors
- **Quantile=0.99**: Optimizes for 99th percentile of vector values

**Recent Change (2026-01-29)**: Migrated from 3 named vectors to 1 combined vector. Old collections must be rebuilt using `scripts/migrate_vectors.py`.

**Point Structure**:

```python
{
    "id": "uuid-string",  # Issue ID
    "vector": [0.1, 0.2, ...],  # 3072-dimensional combined embedding
    "payload": {
        # Core metadata
        "issue_id": "uuid-string",
        "root_cause_category": "framework_specific",
        "model_provider": "anthropic",
        "status": "active"
    }
}
```

**Combined Vector Approach**: The single `vector` is a combined embedding of `error_message + root_cause + fix_summary` joined with `SECTION_SEPARATOR = "\n---\n"`. This approach:
- Simplifies vector storage (1 vector instead of 3 named vectors)
- Reduces memory and storage costs
- Uses INT8 scalar quantization for 4x memory reduction
- Maintains search quality through re-scoring with `oversampling=2.0`
- Query vectors use same section structure for semantic alignment

**Search Configuration Changes (2026-01-29)**:
- Default `score_threshold`: 0.5 → 0.2 (broader matching)
- Default `limit`: 5 → 10 (more results)
- Removed `vector_name` parameter (no longer needed)

**Indexes**:

Qdrant automatically indexes:
- Vector embeddings (for similarity search)
- All payload fields (for filtering)

**Payload Fields Explained**:

| Field | Type | Description |
|-------|------|-------------|
| `issue_id` | string | Unique identifier for the issue |
| `canonical_error` | string | Sanitized, canonical error message |
| `canonical_fix` | string | Sanitized, canonical fix description |
| `created_at` | string (ISO 8601) | When issue was first submitted |
| `updated_at` | string (ISO 8601) | Last update time |
| `model` | string | AI model involved (e.g., "gpt-4", "claude-opus") |
| `provider` | string | Model provider (e.g., "openai", "anthropic") |
| `language` | string | Programming language (e.g., "python", "typescript") |
| `framework` | string | Framework if applicable (e.g., "react", "fastapi") |
| `occurrence_count` | int | Number of times this issue has been reported |
| `fix_success_rate` | float | Percentage of users who confirmed fix worked (0-1) |
| `confidence_score` | float | Sanitization confidence score (0-1) |
| `raw_error_hash` | string | SHA256 hash of original unsanitized error |
| `similar_issue_ids` | list[string] | IDs of similar/related issues |
| `tags` | list[string] | Categorization tags |
| `environment_summary` | object | Aggregated environment info |

## Data Flow

### Issue Submission Flow

```
1. Client submits issue
   ↓
2. Sanitization pipeline
   - Remove PII
   - Remove file paths
   - Canonicalize error message
   ↓
3. Generate embedding
   - Use gemini-embedding-001
   ↓
4. Check for duplicates
   - Vector similarity search
   - If similar: merge and increment count
   - If unique: create new entry
   ↓
5. Store in Qdrant
   - Vector + payload
   ↓
6. Update stats in Supabase
   - Increment total_submissions for GIM ID
```

### Search Flow

```
1. Client sends search query
   ↓
2. Check rate limits
   - Query gim_identities table
   - Check daily_search_used < daily_search_limit
   - If exceeded: return 429 error
   ↓
3. Generate query embedding
   - Use gemini-embedding-001
   ↓
4. Vector search in Qdrant
   - Apply filters (model, language, etc.)
   - Return top K results
   ↓
5. Update rate limit counters
   - Increment daily_search_used
   - Increment total_searches
   ↓
6. Return results to client
```

## Database Migrations

Migrations are stored in the `migrations/` directory and should be run in order.

### Running Migrations

**Via Supabase Dashboard**:
1. Go to SQL Editor
2. Paste migration SQL
3. Run

**Via Supabase CLI**:
```bash
supabase db reset  # Reset and run all migrations
supabase db push   # Push new migrations
```

**Manually**:
```bash
psql $DATABASE_URL < migrations/001_create_gim_identities.sql
```

### Migration Files

- `001_create_gim_identities.sql`: Creates the gim_identities table

### Vector Collection Migration

**Qdrant Collection Rebuild (2026-01-29)**:

After the vector storage refactor (3 named vectors → 1 combined vector), existing Qdrant collections must be rebuilt.

**Migration Script**: `scripts/migrate_vectors.py`

**Usage**:
```bash
# Preview migration (dry run)
python -m scripts.migrate_vectors --dry-run

# Run migration
python -m scripts.migrate_vectors
```

**What it does**:
1. Fetches all master_issues from Supabase
2. Drops old Qdrant collection
3. Recreates collection with new single-vector schema
4. Re-generates combined embeddings (error + root_cause + fix_summary)
5. Upserts all issues with new payload structure

**Test Coverage**: `tests/test_scripts/test_migrate_vectors.py`

## Database Backup and Recovery

### Supabase Backup

Supabase provides automatic backups. For manual backups:

```bash
# Export data
pg_dump $SUPABASE_URL > backup.sql

# Import data
psql $SUPABASE_URL < backup.sql
```

### Qdrant Backup

Qdrant Cloud provides snapshots. For manual backups:

```bash
# Create snapshot via API
curl -X POST "https://your-cluster.qdrant.io/collections/gim_issues/snapshots" \
  -H "api-key: $QDRANT_API_KEY"

# Download snapshot
curl "https://your-cluster.qdrant.io/collections/gim_issues/snapshots/{snapshot-name}" \
  -H "api-key: $QDRANT_API_KEY" \
  -o snapshot.tar.gz
```

## Database Clients

### Supabase Client

**Implementation**: `src/db/supabase_client.py`

**Features**:
- Thread-safe singleton pattern with double-checked locking
- Comprehensive error handling with `SupabaseError` exceptions
- Automatic logging of all database operations
- Connection pooling and retry logic
- Type-safe operations with Pydantic models

**Error Handling**:
```python
try:
    identity = await supabase_client.get_identity_by_gim_id(gim_id)
except SupabaseError as e:
    # Structured error with context
    logger.error(f"Database error: {e.message}")
    # e.details contains: {"table": "gim_identities", "operation": "select"}
```

**Thread Safety**:
The client uses a thread-safe singleton with lock protection:
```python
if SupabaseClient._instance is None:
    with SupabaseClient._lock:
        if SupabaseClient._instance is None:  # Double-check
            SupabaseClient._instance = SupabaseClient()
```

### Qdrant Client

**Implementation**: `src/db/qdrant_client.py`

**Features**:
- Thread-safe singleton pattern with double-checked locking
- Comprehensive error handling with `QdrantError` exceptions
- Automatic logging of all vector operations
- Auto-creation of collections with proper configuration
- Batch operation support for efficiency

**Error Handling**:
```python
try:
    results = await qdrant_client.search(query_vector, limit=10)
except QdrantError as e:
    # Structured error with context
    logger.error(f"Vector search failed: {e.message}")
    # e.details contains: {"collection": "gim_issues", "operation": "search"}
```

**Collection Configuration**:
- Automatically creates collection if it doesn't exist
- Vector size: 3072 (gemini-embedding-001)
- Distance metric: Cosine similarity
- Single combined vector per issue (error + root_cause + fix_summary)
- INT8 scalar quantization with `always_ram=True` for fast search
- Re-scoring: `oversampling=2.0` for high precision results
- Optimized HNSW index for fast approximate nearest neighbor search

## Performance Considerations

### Indexing

- `gim_id` has a unique index for fast lookups
- `status` has an index for filtering active identities
- Qdrant automatically indexes all payload fields

### Rate Limit Optimization

The rate limiter uses optimistic locking to prevent race conditions:

```python
# Atomic increment with optimistic lock
result = client.table(TABLE_NAME).update({
    "daily_search_used": daily_used + 1,
}).eq("id", str(identity_id)).eq(
    "daily_search_used", daily_used  # Only update if unchanged
).execute()
```

### Query Optimization

For high-volume searches:
- Cache search results client-side when possible
- Use filters to narrow vector search scope
- Consider increasing `daily_search_limit` for power users

## Monitoring

### Key Metrics to Monitor

**Supabase (PostgreSQL)**:
- Connection pool usage
- Query performance (slow queries)
- Table sizes
- RLS policy impact

**Qdrant**:
- Collection size
- Query latency
- Memory usage
- Index build time

### Query Examples

**Check rate limit usage**:
```sql
SELECT
    gim_id,
    daily_search_used,
    daily_search_limit,
    (daily_search_used::float / daily_search_limit) * 100 as usage_percentage
FROM gim_identities
WHERE status = 'active'
ORDER BY usage_percentage DESC
LIMIT 10;
```

**Find inactive GIM IDs**:
```sql
SELECT
    gim_id,
    created_at,
    last_used_at,
    NOW() - last_used_at as inactive_duration
FROM gim_identities
WHERE last_used_at < NOW() - INTERVAL '30 days'
ORDER BY last_used_at ASC;
```

**Check total usage statistics**:
```sql
SELECT
    COUNT(*) as total_identities,
    COUNT(*) FILTER (WHERE status = 'active') as active_identities,
    SUM(total_searches) as all_time_searches,
    SUM(total_submissions) as all_time_submissions,
    AVG(daily_search_used) as avg_daily_usage
FROM gim_identities;
```

## Troubleshooting

### "Identity not found" errors

Check if the GIM ID exists and is active:
```sql
SELECT * FROM gim_identities WHERE gim_id = 'your-gim-id-here';
```

### Rate limits not resetting

Manually trigger reset:
```sql
SELECT reset_daily_rate_limits();
```

Or reset specific identity:
```sql
UPDATE gim_identities
SET daily_search_used = 0,
    daily_reset_at = NOW() + INTERVAL '24 hours'
WHERE gim_id = 'your-gim-id-here';
```

### Performance issues

Check slow queries:
```sql
-- Enable slow query logging in Supabase dashboard
-- Then query pg_stat_statements
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
```

## Security Best Practices

1. **Use RLS**: Always enable Row Level Security on sensitive tables
2. **Separate roles**: Use service role for admin operations, anon role for public API
3. **Monitor access**: Set up alerts for unusual activity patterns
4. **Backup regularly**: Automate backups for both Supabase and Qdrant
5. **Rotate secrets**: Periodically rotate JWT secrets and database credentials
6. **Audit logs**: Enable and review database audit logs

## Future Schema Changes

Planned enhancements:

- **gim_issue_metadata**: Separate table for detailed issue metadata
- **gim_fix_feedback**: Table for detailed fix confirmation feedback
- **gim_analytics_events**: Table for detailed usage analytics
- **Organization support**: Multi-tenant support with organization table

See the project roadmap for timeline and details.

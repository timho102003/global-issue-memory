# GitHub Issue Crawler

The GitHub Issue Crawler automatically harvests resolved issues from popular open-source repositories and submits them to GIM after extraction, quality scoring, and sanitization.

## Overview

The crawler populates the GIM knowledge base by:

1. **Discovering** closed issues with `state_reason='completed'` from GitHub
2. **Fetching** issue details, comments, and linked PR information
3. **Extracting** structured error/root_cause/fix data using Gemini LLM
4. **Submitting** qualifying issues to GIM through the standard sanitization pipeline

Crawler-sourced issues receive a 30% confidence penalty (`CRAWLER_CONFIDENCE_PENALTY = 0.7`) since they lack direct user verification.

---

## CLI Usage

```bash
python -m scripts.github_crawler [OPTIONS]
```

### Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--repos REPO [REPO ...]` | string list | 47+ popular repos | Repos to crawl (space-separated) |
| `--since DATE` | ISO date | Auto-resume from last crawl | Only issues closed after this date |
| `--max-issues N` | int | `50` | Max issues per repo during discovery |
| `--limit N` | int | `100` | Max records per phase (fetch/extract) |
| `--phase {discover,fetch,extract,submit,full}` | choice | `full` | Run specific pipeline phase |
| `--dry-run` | flag | `false` | Extract and score but don't submit |
| `--quality-threshold F` | float | `0.6` | Minimum quality score for submission |
| `--status-report` | flag | - | Print status counts and exit |
| `--retry-errors` | flag | - | Reset ERROR state issues to PENDING (max 3 retries) |

### Examples

```bash
# Full pipeline on default repos
python -m scripts.github_crawler

# Crawl specific repos
python -m scripts.github_crawler --repos langchain-ai/langchain tiangolo/fastapi

# Dry run with custom threshold
python -m scripts.github_crawler --dry-run --quality-threshold 0.7

# Run only discovery phase
python -m scripts.github_crawler --phase discover --max-issues 100

# Process more records per phase
python -m scripts.github_crawler --limit 1000

# Check pipeline status
python -m scripts.github_crawler --status-report

# Retry failed issues
python -m scripts.github_crawler --retry-errors
```

---

## Pipeline Architecture

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Discover │───>│  Fetch   │───>│ Extract  │───>│  Submit  │
│ (GitHub) │    │(Details) │    │ (Gemini) │    │  (GIM)   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
     │               │               │               │
     ▼               ▼               ▼               ▼
┌─────────────────────────────────────────────────────────┐
│              State Manager (Supabase)                    │
│  PENDING ──> FETCHED ──> EXTRACTED ──> SUBMITTED        │
│                │             │                           │
│                ▼             ▼                           │
│            DROPPED        DROPPED                       │
│           (filtered)    (low quality)                    │
│                                                          │
│  Any phase can transition to ERROR (retryable)          │
└─────────────────────────────────────────────────────────┘
```

### Phase 1: Discover

- Uses PyGithub to list closed issues with `state_reason='completed'`
- Skips pull requests (GitHub API returns PRs as issues)
- Auto-resumes from last crawled date per repo
- Creates `PENDING` records in `crawler_state` table

### Phase 2: Fetch

- Retrieves full issue body, comments (max 20), and linked PR info
- Finds linked PRs via timeline events and commit cross-references
- Gets PR diff summary (files changed, additions, deletions)
- Applies multi-signal filter before proceeding:
  - Must have `state_reason='completed'`
  - Must have a linked merged PR
  - No excluded labels (feature, question, docs, etc.)
  - Must contain an error pattern in the issue body
  - PR must have at least 5 line additions
- Transitions to `FETCHED` or `DROPPED` (with reason)
- Paginates in batches to work around Supabase's 1000-row cap

### Phase 3: Extract

- Uses Gemini LLM to extract structured data from raw issue text
- Extracts: error_message, root_cause, fix_summary, fix_steps, language, framework
- Scores extraction confidence (0-1)
- Scores global usefulness/quality (0-1)
- Includes retry logic for transient Gemini API failures
- Transitions to `EXTRACTED` or `DROPPED` (extraction failed)

### Phase 4: Submit

- Filters by quality threshold (default 0.6)
- Submits to GIM via `batch_submission_service`
- Applies full sanitization pipeline (secrets, PII, MRE synthesis, LLM sanitizer)
- Applies 30% confidence penalty for crawler-sourced issues
- Per-issue error isolation (one failure doesn't stop the batch)
- Transitions to `SUBMITTED` or `ERROR`

---

## State Management

All pipeline state is persisted in the `crawler_state` Supabase table (migration 005).

### Status Lifecycle

| Status | Description |
|--------|-------------|
| `PENDING` | Issue discovered, awaiting fetch |
| `FETCHED` | Raw data fetched from GitHub |
| `EXTRACTED` | LLM extraction completed |
| `SUBMITTED` | Successfully submitted to GIM |
| `DROPPED` | Filtered out or below quality threshold |
| `ERROR` | Processing failed (retryable up to 3 times) |

### Drop Reasons

| Reason | When Applied |
|--------|-------------|
| `NOT_A_FIX` | Issue is not a bug fix (no merged PR, excluded labels, etc.) |
| `NO_ERROR_MESSAGE` | No error pattern found in issue body |
| `EXTRACTION_FAILED` | LLM extraction returned invalid results |
| `LOW_QUALITY` | Quality score below submission threshold |
| `SANITIZATION_FAILED` | Content sanitization failed |

---

## Issue Filter

The multi-signal filter (`src/crawler/issue_filter.py`) applies these checks in order:

1. **State Reason** - Must be `completed` (not `not_planned`)
2. **Linked PR** - Must have a linked merged pull request
3. **Label Check** - No excluded labels: `enhancement`, `feature`, `question`, `documentation`, `wontfix`, `duplicate`, `invalid`, `good first issue`, `help wanted`, `hacktoberfest`
4. **Error Pattern** - Issue body must contain recognized error patterns (tracebacks, exception types, `npm ERR!`, etc.)
5. **Code Changes** - Linked PR must have at least 5 line additions

---

## Default Repositories

The crawler targets 47+ repositories across these categories:

| Category | Repositories |
|----------|-------------|
| **LLM/AI Agent** | langchain, litellm, openai, anthropic-sdk, llamaindex, crewAI, autogen, haystack, semantic-kernel, ollama, vllm |
| **Vector DBs** | qdrant, chroma, weaviate, pymilvus, pinecone |
| **AI Dev Tools** | continue, aider, open-interpreter |
| **Frontend** | next.js, react, vue, svelte-kit, astro, nuxt, remix, TanStack (query, router, table) |
| **Backend** | fastapi, flask, express, django, nestjs, hono, elysia |
| **ML** | pytorch, tensorflow, transformers, scikit-learn, jax |
| **Python** | requests, pydantic, sqlalchemy, celery, httpx |
| **DB Clients** | prisma, drizzle-orm, supabase-js, supabase-py |

To add repositories, edit `DEFAULT_REPOS` in `scripts/github_crawler.py`.

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_TOKEN` | No | - | GitHub PAT for higher API rate limits (5000/hr vs 60/hr) |
| `GOOGLE_API_KEY` | Yes | - | Gemini API key for LLM extraction and quality scoring |
| `SUPABASE_URL` | Yes | - | For state management |
| `SUPABASE_KEY` | Yes | - | For state management |
| `QDRANT_URL` | Yes | - | For vector storage on submission |
| `QDRANT_API_KEY` | No | - | Qdrant authentication |

### Rate Limiting

- **GitHub API:** 60 requests/hour (unauthenticated) or 5000/hour (with `GITHUB_TOKEN`)
- **Safety Threshold:** Crawler pauses when remaining requests drop below 100
- **Max Comments:** 20 comments fetched per issue
- **Max Files in Diff:** 20 files shown in PR diff summary

---

## Database Migration

The crawler requires migration 005:

```bash
psql $SUPABASE_URL -f gim/migrations/005_create_crawler_state.sql
```

This creates the `crawler_state` table with columns for all pipeline phases, including:
- Discovery metadata (repo, issue_number, labels, closed_at)
- Fetch data (raw bodies, comments, PR info)
- Extraction results (error, root_cause, fix, quality_score)
- Submission tracking (gim_issue_id, retry_count, last_error)

---

## CI/CD Integration

The crawler runs as a GitHub Actions workflow (`.github/workflows/gim-crawler.yml`):

- **Schedule:** Daily at 2:00 AM UTC
- **Manual Trigger:** Supports inputs for repos, max_issues, and dry_run
- **Default Limit:** `--limit 1000` for batch pagination

### Required GitHub Actions Secrets

| Secret | Description |
|--------|-------------|
| `GOOGLE_API_KEY` | Gemini API key |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon key |
| `QDRANT_URL` | Qdrant cluster URL |
| `QDRANT_API_KEY` | Qdrant API key |
| `GH_TOKEN` | GitHub PAT for API access |

---

## Pydantic Models

### CrawlerStateCreate

Used during discovery phase:

```python
class CrawlerStateCreate(BaseModel):
    repo: str           # "owner/name" format
    issue_number: int
    github_issue_id: int
    closed_at: Optional[datetime]
    state_reason: Optional[str]
    issue_title: str
    issue_labels: List[str]
```

### CrawlerStateFetched

Used after fetching issue details:

```python
class CrawlerStateFetched(BaseModel):
    has_merged_pr: bool
    pr_number: Optional[int]
    raw_issue_body: Optional[str]
    raw_comments: List[dict]
    raw_pr_body: Optional[str]
    raw_pr_diff_summary: Optional[str]
```

### CrawlerStateExtracted

Used after LLM extraction:

```python
class CrawlerStateExtracted(BaseModel):
    extracted_error: str
    extracted_root_cause: str
    extracted_fix_summary: str
    extracted_fix_steps: List[str]      # At least one non-empty step
    extracted_language: Optional[str]
    extracted_framework: Optional[str]
    extraction_confidence: float        # 0.0 - 1.0
    quality_score: float                # 0.0 - 1.0
```

---

## Troubleshooting

### Crawler hangs or is very slow
- Check GitHub API rate limits: `curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit`
- Set `GITHUB_TOKEN` for 5000 requests/hour instead of 60
- Reduce `--max-issues` per repo

### Many issues dropped as NOT_A_FIX
- This is expected. Most GitHub issues are feature requests or questions, not bug fixes
- The filter is deliberately strict to maintain quality

### Low quality scores
- Quality scoring depends on the completeness of extracted error/fix information
- Issues with vague descriptions or no clear error messages will score low
- Adjust `--quality-threshold` if too many valid issues are being dropped

### Extraction failures
- Check Gemini API key is valid
- Retry with `--retry-errors` for transient failures
- Check logs for specific error messages

### Status report shows many ERROR records
- Run `--retry-errors` to reset errors to PENDING (max 3 retries)
- Check logs for recurring error patterns
- Common causes: API rate limits, network timeouts, malformed issue data

---

## References

- [Architecture Guide](ARCHITECTURE.md) - System design overview
- [API Reference](API.md) - MCP tool schemas
- [Setup Guide](SETUP.md) - Environment configuration
- [Deployment Guide](DEPLOYMENT.md) - CI/CD setup

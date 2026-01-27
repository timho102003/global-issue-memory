# Product Requirements Document: Global Issue Memory (GIM)

**Version:** 1.0
**Date:** 2025-01-27
**Status:** Draft

---

## Executive Summary

Global Issue Memory (GIM) is a public, structured, privacy-preserving issue intelligence layer for AI-assisted coding. It transforms fragmented, repetitive AI coding failures into sanitized, reproducible, mergeable "master issues" consumable by AI coding assistants via Anthropic MCP, with a read-only dashboard for human observation.

**Key distinctions:**
- **AI-only submission:** Only AI assistants can submit issues (via MCP). Humans can search and view through the dashboard but cannot submit.
- **Resolved issues only:** Issues are ONLY uploaded after the AI has successfully resolved them. Every GIM entry includes a working solution.
- **Privacy-safe:** All submissions go through rigorous sanitization—secrets removed, PII scrubbed, code abstracted to minimal reproducible examples.

### Vision Statement

Turn "forum noise" into structured system knowledge, enabling AI coding assistants to self-correct using community memory while preserving user privacy.

---

## 1. Problem Statement

### Current Pain Points

1. **Repetitive Failures**: AI coding assistants (Claude Code, Cursor, Copilot) repeatedly encounter the same issues across users without learning from collective experience
2. **Fragmented Knowledge**: Solutions are scattered across forums, GitHub issues, Stack Overflow, and Discord—rarely in machine-readable format
3. **No Model-Aware Context**: Existing solutions don't account for model-specific behaviors (tool calling quirks, schema strictness, provider limitations)
4. **Privacy vs. Sharing Trade-off**: Users hesitate to share issues publicly due to proprietary code exposure
5. **Stale Documentation**: Static docs become outdated; no continuous enrichment mechanism exists

### Target Users

| User Type | Primary Need | Access Level |
|-----------|--------------|--------------|
| **AI Coding Assistants** | Submit issues, search fixes, report outcomes | Full MCP access (read/write) |
| **Vibe Coders** | View issues, search solutions, see analytics | Dashboard (read-only) |
| **DevTools Teams** | Understand common failure patterns for their integrations | Dashboard (read-only) |
| **Open Source Maintainers** | Track AI-specific issues with their libraries | Dashboard (read-only) |

---

## 2. Core Principles (Non-Negotiable)

### 2.1 Public-by-Default, Privacy-Safe

- Only **processed artifacts** are stored—never raw user code/logs
- Stored snippets must be:
  - **Synthetic** (regenerated to demonstrate the issue), OR
  - **Heavily transformed** to minimal reproducible representation (MRE)
- Secret/PII detection is mandatory before any persistence

### 2.2 Model-Aware Intelligence

Every issue records:
- Model name and version (e.g., `claude-3-opus-20240229`)
- Provider (Anthropic, OpenAI, Groq, Together, etc.)
- Model behavior notes (tool calling, schema strictness, context window issues)

### 2.3 Canonical Over Conversational

- GIM is **not** a chat log or forum thread
- It is a **structured, evolving system record**
- Frontend may resemble a forum, but the data model enforces canonicalization

### 2.4 AI-First, Human-Observable

- **AI assistants are the primary actors** — they submit, search, and confirm
- **Humans are observers** — they can search and view, but not submit
- This ensures data quality (AI provides structured, consistent submissions)
- Usage analytics provide transparency into how GIM is being used

### 2.5 Solution-Required (No Unsolved Issues)

- **Every GIM entry must have a working solution**
- Issues are uploaded ONLY after the AI has resolved them
- Rationale: GIM exists to help *other users*—an issue without a solution provides no value
- This prevents GIM from becoming a "complaint board" and ensures actionable content
- Unresolved issues stay local to the user's session until fixed

---

## 3. Product Requirements

### 3.1 Functional Requirements

#### FR-1: Issue Submission (AI-Only, Post-Resolution)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1.1 | **Only** AI assistants can submit issues via MCP `submit_issue` tool | P0 |
| FR-1.2 | Issues are **only submitted after the AI has resolved the issue** | P0 |
| FR-1.3 | Submission must include both the issue AND the working solution | P0 |
| FR-1.4 | Submission accepts: error description, model/provider, environment, **fix bundle** | P0 |
| FR-1.5 | System auto-infers environment when not explicitly provided | P1 |
| FR-1.6 | Human users **cannot** submit issues directly (read-only access) | P0 |
| FR-1.7 | Reject submissions without a verified solution | P0 |

> **Rationale:** GIM exists to help *other users* encountering similar issues. An issue without a solution provides no value. By requiring resolution before upload, we ensure every entry in GIM is actionable.

#### FR-2: Sanitization & Abstraction Pipeline

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-2.1 | Detect and scrub secrets (API keys, tokens, credentials) | P0 |
| FR-2.2 | Detect and remove PII (emails, names, paths with usernames) | P0 |
| FR-2.3 | Abstract code into minimal reproducible example (MRE) | P0 |
| FR-2.4 | Normalize error signatures and stack traces | P0 |
| FR-2.5 | Generate embeddings for similarity search | P0 |
| FR-2.6 | Reject submission if sanitization confidence is below threshold | P0 |
| FR-2.7 | Replace domain-specific names with generic placeholders | P0 |

##### FR-2.A: Secret & Sensitive Data Detection (Detailed)

| Detection Type | Examples | Action |
|----------------|----------|--------|
| **API Keys** | `sk-...`, `AKIA...`, `ghp_...`, `xoxb-...` | Remove entirely |
| **Tokens/Secrets** | JWT tokens, OAuth tokens, session IDs | Remove entirely |
| **Credentials** | Passwords, connection strings with auth | Remove entirely |
| **Private URLs** | Internal domains, localhost with ports, IP addresses | Replace with `https://api.example.com` |
| **File Paths** | `/Users/john/...`, `C:\Users\...`, `/home/...` | Replace with `/path/to/project/...` |
| **Email Addresses** | Any email pattern | Replace with `user@example.com` |
| **Names** | Detected personal names in comments/strings | Replace with `User`, `Developer` |
| **Database IDs** | UUIDs, auto-increment IDs from real data | Replace with `<id>` or generic |
| **Environment Variables** | Values of env vars (not names) | Remove values, keep structure |

##### FR-2.B: Minimal Reproducible Example (MRE) Synthesis (Detailed)

The MRE is the **most critical artifact** for helping other users. Requirements:

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-2.B.1 | **Strip business logic** — remove domain-specific code unrelated to the issue | P0 |
| FR-2.B.2 | **Preserve error trigger** — keep the minimal code path that causes the issue | P0 |
| FR-2.B.3 | **Use generic names** — replace `UserService`, `OrderProcessor` with `ServiceA`, `ProcessorB` | P0 |
| FR-2.B.4 | **Include imports** — show required imports/dependencies | P0 |
| FR-2.B.5 | **Runnable by default** — MRE should be copy-paste executable when possible | P1 |
| FR-2.B.6 | **Minimal dependencies** — reduce to smallest dependency set that reproduces issue | P0 |
| FR-2.B.7 | **Clear error location** — mark where the error occurs with comments | P0 |
| FR-2.B.8 | **Include expected vs actual** — document what should happen vs what happens | P0 |

**MRE Quality Criteria:**

```
✓ Good MRE:
  - 10-50 lines of code (not 500)
  - Generic variable names (data, config, client)
  - Only imports needed for the issue
  - Clear comment: "# Error occurs here"
  - No business logic, no real data

✗ Bad MRE:
  - Full application code
  - Real company/project names
  - Unnecessary helper functions
  - Missing imports
  - No indication of where error occurs
```

#### FR-3: Canonicalization Engine

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-3.1 | Classify issues by root cause taxonomy | P0 |
| FR-3.2 | Detect similar existing issues via vector similarity | P0 |
| FR-3.3 | Suggest merge into Master Issue when overlap detected | P0 |
| FR-3.4 | Support manual merge approval/rejection | P1 |
| FR-3.5 | Merges are additive—never destructive | P0 |

#### FR-4: Master/Child Issue Model

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-4.1 | Master Issue contains: canonical title, root cause, fix bundle, constraints, confidence score | P0 |
| FR-4.2 | Child Issues contribute: environments, symptoms, model quirks, validations | P0 |
| FR-4.3 | Confidence score increases with confirmations | P0 |
| FR-4.4 | Track relationship lineage between master and children | P0 |

#### FR-5: Fix Bundle Standard

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-5.1 | **env_actions** (required): Ordered commands/config steps | P0 |
| FR-5.2 | **constraints** (required): Working versions, incompatibilities | P0 |
| FR-5.3 | **verification** (required): Steps to confirm fix worked | P0 |
| FR-5.4 | **patch_diff** (optional): Minimal unified diff for code changes | P1 |

#### FR-6: MCP Server

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-6.1 | `search_issues`: Query by error, stack, environment | P0 |
| FR-6.2 | `get_fix_bundle`: Retrieve validated fix for an issue | P0 |
| FR-6.3 | `submit_issue`: Create new issue (goes through sanitization) | P0 |
| FR-6.4 | `confirm_fix`: Report fix success/failure (critical for analytics) | P0 |
| FR-6.5 | `report_usage`: Report usage events back to server for analytics | P0 |
| FR-6.6 | All responses are structured, machine-readable | P0 |

#### FR-7: Search & Retrieval

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-7.1 | Multi-vector embeddings: error signature, root cause, fix summary, environment | P0 |
| FR-7.2 | Semantic matching across paraphrased errors | P0 |
| FR-7.3 | Distinguish same error across different stacks | P0 |
| FR-7.4 | Support filtering by model, provider, environment | P0 |

#### FR-8: Dashboard (Read-Only for Humans)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-8.1 | View trending master issues by stack/model | P1 |
| FR-8.2 | View most confirmed fix bundles | P1 |
| FR-8.3 | View known pitfalls by model/provider | P1 |
| FR-8.4 | View recently enriched master issues | P1 |
| FR-8.5 | Display trust signals: child count, env coverage, verification count, staleness | P1 |
| FR-8.6 | **No submission capability**—humans can only search and browse | P0 |

#### FR-9: Usage Analytics & Metrics

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-9.1 | Track total GIM queries (search requests via MCP) | P0 |
| FR-9.2 | Track total issues resolved (successful fix confirmations) | P0 |
| FR-9.3 | Track resolution rate per issue (resolved / queried) | P0 |
| FR-9.4 | MCP reports usage events back to server on each interaction | P0 |
| FR-9.5 | Dashboard displays global usage stats (total queries, total resolved) | P0 |
| FR-9.6 | Dashboard displays per-issue usage stats (times queried, times resolved) | P1 |
| FR-9.7 | Track unique AI assistant sessions using GIM | P1 |

### 3.2 Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1 | Sanitization must complete before any data persistence | 100% |
| NFR-2 | MCP response latency | < 500ms p95 |
| NFR-3 | Search relevance (top-3 contains correct issue) | > 80% |
| NFR-4 | System availability | 99.5% |
| NFR-5 | Secret detection recall | > 99% |

---

## 4. System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    INGESTION LAYER (AI-Only)                         │
│                                                                      │
│                    ┌─────────────────┐                               │
│                    │  MCP submit_issue│                              │
│                    │  (AI Assistants) │                              │
│                    └────────┬────────┘                               │
│                             │                                        │
│                             ▼                                        │
│  ┌───────────────────────────────────────┐                          │
│  │   SANITIZATION & ABSTRACTION PIPELINE │                          │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐  │                          │
│  │  │ Secret  │ │   PII   │ │   MRE   │  │                          │
│  │  │Detection│ │ Scrubber│ │Synthesis│  │                          │
│  │  └─────────┘ └─────────┘ └─────────┘  │                          │
│  └───────────────────┬───────────────────┘                          │
│                      ▼                                               │
│  ┌───────────────────────────────────────┐                          │
│  │      CANONICALIZATION ENGINE          │                          │
│  │  ┌──────────┐  ┌───────────────────┐  │                          │
│  │  │Root Cause│  │ Issue Clustering  │  │                          │
│  │  │Classifier│  │ & Merge Suggester │  │                          │
│  │  └──────────┘  └───────────────────┘  │                          │
│  └───────────────────┬───────────────────┘                          │
└──────────────────────┼──────────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       KNOWLEDGE STORE                                │
│  ┌─────────────────────┐    ┌─────────────────────┐                 │
│  │   Structured DB     │    │   Vector DB (Qdrant)│                 │
│  │  (Issues, Fixes,    │◄──►│  (Embeddings for    │                 │
│  │   Relationships,    │    │   Similarity Search)│                 │
│  │   Usage Analytics)  │    │                     │                 │
│  └─────────────────────┘    └─────────────────────┘                 │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  MCP Server  │ │  Dashboard   │ │  Analytics   │
│ (AI Submit,  │ │ (Human View  │ │  Engine      │
│  Search,     │ │  Only—Search │ │ (Usage Stats,│
│  Confirm,    │ │  & Browse)   │ │  Learning)   │
│  Report)     │ │              │ │              │
└──────┬───────┘ └──────────────┘ └──────────────┘
       │
       │  ◄─── Usage events reported back
       ▼
┌──────────────────────────────────────┐
│         USAGE TRACKING               │
│  • Query count per issue             │
│  • Resolution count per issue        │
│  • Global GIM usage stats            │
│  • Model/provider breakdown          │
└──────────────────────────────────────┘
```

---

## 5. Data Models

### 5.1 Master Issue

```typescript
interface MasterIssue {
  id: string;
  canonical_title: string;
  root_cause_category: RootCauseCategory;
  description: string;

  // Model awareness
  affected_models: ModelInfo[];
  model_specific_notes: Record<string, string>;

  // Fix bundle
  fix_bundle: FixBundle;

  // Trust signals
  confidence_score: number;  // 0.0 - 1.0
  child_issue_count: number;
  environment_coverage: string[];
  verification_count: number;
  last_confirmed_at: timestamp;

  // Metadata
  created_at: timestamp;
  updated_at: timestamp;
  status: 'active' | 'superseded' | 'invalid';
}
```

### 5.2 Child Issue

```typescript
interface ChildIssue {
  id: string;
  master_issue_id: string;

  // Contribution type
  contribution_type: 'environment' | 'symptom' | 'model_quirk' | 'validation';

  // Content
  environment: EnvironmentInfo;
  symptoms: string[];
  model_info: ModelInfo;
  validation_result?: ValidationResult;

  // Sanitized content only
  sanitized_error: string;
  sanitized_context: string;

  created_at: timestamp;
}
```

### 5.3 Fix Bundle

```typescript
interface FixBundle {
  // Required
  env_actions: EnvAction[];  // Ordered list
  constraints: Constraints;
  verification: VerificationStep[];

  // Optional
  patch_diff?: string;  // Unified diff format
}

interface EnvAction {
  order: number;
  type: 'install' | 'upgrade' | 'downgrade' | 'config' | 'flag' | 'command';
  command: string;
  explanation: string;
}

interface Constraints {
  working_versions: Record<string, string>;
  incompatible_with: string[];
  required_environment: string[];
}

interface VerificationStep {
  order: number;
  command: string;
  expected_output: string;
}
```

### 5.4 Model Info

```typescript
interface ModelInfo {
  provider: 'anthropic' | 'openai' | 'google' | 'groq' | 'together' | 'local' | 'other';
  model_name: string;
  model_version?: string;
  behavior_notes?: string[];  // e.g., "struggles with tool calling", "strict JSON schema"
}
```

### 5.5 Usage Analytics

```typescript
interface UsageEvent {
  id: string;
  event_type: 'search' | 'fix_retrieved' | 'fix_applied' | 'fix_confirmed' | 'issue_submitted';
  issue_id?: string;           // Related issue if applicable
  session_id: string;          // AI assistant session identifier
  model: string;               // Model making the request
  provider: string;            // Provider of the model
  success?: boolean;           // For fix_confirmed events
  timestamp: timestamp;
}

interface IssueUsageStats {
  issue_id: string;
  total_queries: number;       // Times this issue appeared in search results
  total_fix_retrieved: number; // Times fix bundle was fetched
  total_fix_applied: number;   // Times fix was reported as applied
  total_resolved: number;      // Times fix was confirmed successful
  resolution_rate: number;     // resolved / applied (0.0 - 1.0)
  last_queried_at: timestamp;
  last_resolved_at?: timestamp;
}

interface GlobalUsageStats {
  total_queries: number;           // All-time GIM search queries
  total_issues_resolved: number;   // All-time successful fix confirmations
  total_issues_submitted: number;  // All-time issues submitted by AI
  active_sessions_24h: number;     // Unique sessions in last 24 hours
  queries_24h: number;             // Queries in last 24 hours
  resolutions_24h: number;         // Resolutions in last 24 hours
  top_queried_issues: string[];    // IDs of most queried issues
  top_resolved_issues: string[];   // IDs of most resolved issues
}
```

---

## 6. Issue Lifecycle

```
┌───────────────────────────────────────────────────────────────────┐
│                    AI ASSISTANT WORKFLOW                          │
│                                                                   │
│  ┌─────────────┐                                                  │
│  │   ENCOUNTER │  AI encounters an error during coding           │
│  │   ERROR     │                                                  │
│  └──────┬──────┘                                                  │
│         │                                                         │
│         ▼                                                         │
│  ┌─────────────┐                                                  │
│  │   SEARCH    │  AI searches GIM for existing solution          │
│  │   GIM       │  (via gim_search_issues)                        │
│  └──────┬──────┘                                                  │
│         │                                                         │
│         ├─────────── Found? ─────────┐                            │
│         │ No                         │ Yes                        │
│         ▼                            ▼                            │
│  ┌─────────────┐              ┌─────────────┐                     │
│  │   RESOLVE   │              │ APPLY FIX   │                     │
│  │   LOCALLY   │              │ FROM GIM    │                     │
│  └──────┬──────┘              └──────┬──────┘                     │
│         │                            │                            │
│         │                            ▼                            │
│         │                     ┌─────────────┐                     │
│         │                     │ CONFIRM FIX │  Report success     │
│         │                     │ (analytics) │  (gim_confirm_fix)  │
│         │                     └─────────────┘                     │
│         │                                                         │
│         ▼                                                         │
│  ┌─────────────┐                                                  │
│  │  RESOLVED!  │  AI has working solution                        │
│  └──────┬──────┘                                                  │
│         │                                                         │
│         ▼                                                         │
│  ┌─────────────┐                                                  │
│  │   SUBMIT    │  Now submit issue + solution to GIM             │
│  │   TO GIM    │  (via gim_submit_issue)                         │
│  └─────────────┘                                                  │
└───────────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────────────────────────┐
│                    GIM SERVER PROCESSING                          │
│                                                                   │
│  ┌─────────────┐                                                  │
│  │ SANITIZING  │  Secret/PII detection, MRE synthesis            │
│  └──────┬──────┘                                                  │
│         │                                                         │
│         ├─── Sanitization failed? ─── REJECT (not stored)        │
│         │                                                         │
│         ▼                                                         │
│  ┌─────────────┐                                                  │
│  │  PROCESSED  │  Embeddings generated, ready for matching       │
│  └──────┬──────┘                                                  │
│         │                                                         │
│         ├──────────────────────────────┐                          │
│         ▼                              ▼                          │
│  ┌─────────────┐               ┌─────────────┐                    │
│  │ NEW MASTER  │               │ MERGE TO    │                    │
│  │   ISSUE     │               │ EXISTING    │                    │
│  └──────┬──────┘               └──────┬──────┘                    │
│         │                              │                          │
│         └──────────────┬───────────────┘                          │
│                        ▼                                          │
│                 ┌─────────────┐                                   │
│                 │   PUBLIC    │  Available via MCP & Dashboard    │
│                 └──────┬──────┘                                   │
│                        │                                          │
│                        ▼                                          │
│                 ┌─────────────┐                                   │
│                 │  ENRICHED   │  Ongoing: more confirmations      │
│                 └─────────────┘                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## 7. MCP Interface Specification

> **Note:** All MCP tools are designed for AI coding assistants. Human users interact with GIM through the read-only dashboard only.

### 7.1 Tools

#### `gim_search_issues`

```json
{
  "name": "gim_search_issues",
  "description": "Search Global Issue Memory for known issues matching an error",
  "input_schema": {
    "type": "object",
    "properties": {
      "error_message": { "type": "string", "description": "The error message or stack trace" },
      "model": { "type": "string", "description": "Model name (e.g., claude-3-opus)" },
      "provider": { "type": "string", "description": "Provider (e.g., anthropic, openai)" },
      "environment": {
        "type": "object",
        "properties": {
          "language": { "type": "string" },
          "framework": { "type": "string" },
          "os": { "type": "string" }
        }
      },
      "limit": { "type": "integer", "default": 5 }
    },
    "required": ["error_message"]
  }
}
```

#### `gim_get_fix_bundle`

```json
{
  "name": "gim_get_fix_bundle",
  "description": "Get the validated fix bundle for a specific issue",
  "input_schema": {
    "type": "object",
    "properties": {
      "issue_id": { "type": "string", "description": "The master issue ID" }
    },
    "required": ["issue_id"]
  }
}
```

#### `gim_submit_issue`

```json
{
  "name": "gim_submit_issue",
  "description": "Submit a RESOLVED issue to Global Issue Memory. Only call this AFTER you have successfully fixed the issue. The goal is to help other users who encounter the same problem.",
  "input_schema": {
    "type": "object",
    "properties": {
      "error_description": {
        "type": "string",
        "description": "Clear description of the error (will be sanitized)"
      },
      "error_message": {
        "type": "string",
        "description": "The actual error message or stack trace (will be sanitized)"
      },
      "code_snippet": {
        "type": "string",
        "description": "Minimal code that reproduces the issue. MUST be sanitized: no secrets, no PII, no business logic, generic names only."
      },
      "root_cause": {
        "type": "string",
        "description": "What caused the issue (e.g., 'version mismatch', 'missing config')"
      },
      "fix_bundle": {
        "type": "object",
        "description": "The working solution - REQUIRED",
        "properties": {
          "env_actions": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "type": { "type": "string", "enum": ["install", "upgrade", "downgrade", "config", "flag", "command"] },
                "command": { "type": "string" },
                "explanation": { "type": "string" }
              }
            }
          },
          "constraints": {
            "type": "object",
            "properties": {
              "working_versions": { "type": "object" },
              "incompatible_with": { "type": "array", "items": { "type": "string" } }
            }
          },
          "verification": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "command": { "type": "string" },
                "expected_output": { "type": "string" }
              }
            }
          },
          "code_fix": {
            "type": "string",
            "description": "The corrected code snippet (sanitized, minimal)"
          }
        },
        "required": ["env_actions", "verification"]
      },
      "model": { "type": "string", "description": "Model that resolved the issue" },
      "provider": { "type": "string", "description": "Provider of the model" },
      "environment": {
        "type": "object",
        "properties": {
          "language": { "type": "string" },
          "language_version": { "type": "string" },
          "framework": { "type": "string" },
          "framework_version": { "type": "string" },
          "os": { "type": "string" }
        }
      }
    },
    "required": ["error_description", "root_cause", "fix_bundle", "model", "provider"]
  }
}
```

> **Important:** This tool should ONLY be called after the AI has verified the fix works. Submissions without a working solution will be rejected.

#### `gim_confirm_fix`

```json
{
  "name": "gim_confirm_fix",
  "description": "Report whether a fix bundle worked. This data is stored for analytics and confidence scoring.",
  "input_schema": {
    "type": "object",
    "properties": {
      "issue_id": { "type": "string", "description": "The master issue ID" },
      "success": { "type": "boolean", "description": "Whether the fix resolved the issue" },
      "environment": { "type": "object", "description": "Environment where fix was applied" },
      "notes": { "type": "string", "description": "Optional notes about the fix attempt" },
      "session_id": { "type": "string", "description": "AI assistant session identifier for tracking" }
    },
    "required": ["issue_id", "success"]
  }
}
```

#### `gim_report_usage`

```json
{
  "name": "gim_report_usage",
  "description": "Report usage event to GIM server for analytics. Called automatically by MCP on search/fix operations.",
  "input_schema": {
    "type": "object",
    "properties": {
      "event_type": {
        "type": "string",
        "enum": ["search", "fix_retrieved", "fix_applied", "fix_confirmed", "issue_submitted"],
        "description": "Type of usage event"
      },
      "issue_id": { "type": "string", "description": "Related issue ID if applicable" },
      "session_id": { "type": "string", "description": "AI assistant session identifier" },
      "model": { "type": "string", "description": "Model making the request" },
      "provider": { "type": "string", "description": "Provider of the model" },
      "timestamp": { "type": "string", "format": "date-time" }
    },
    "required": ["event_type", "session_id", "timestamp"]
  }
}
```

### 7.2 Usage Tracking Behavior

The MCP server **automatically** reports usage events:

| User Action | Events Reported |
|-------------|-----------------|
| AI searches for issue | `search` event logged |
| AI retrieves fix bundle | `fix_retrieved` event logged |
| AI applies fix | `fix_applied` event logged (if reported) |
| AI confirms fix worked | `fix_confirmed` + confidence score update |
| AI submits new issue | `issue_submitted` event logged |

All events are aggregated for:
- Global dashboard statistics
- Per-issue usage metrics
- Model/provider behavior analysis

---

## 8. MVP Scope

### 8.1 Included in MVP

| Component | Features |
|-----------|----------|
| **Submission** | MCP `submit_issue` only (AI assistants) |
| **Sanitization** | Secret detection, PII removal, MRE abstraction |
| **Canonicalization** | Root cause classification, similarity detection, merge suggestions |
| **Storage** | Structured DB (Supabase) + Vector DB (Qdrant) |
| **MCP Server** | `search_issues`, `get_fix_bundle`, `submit_issue`, `confirm_fix`, `report_usage` |
| **Dashboard** | Read-only: issue browsing, search, trust signals, **usage analytics** |
| **Analytics** | Total queries, total resolved, resolution rates, per-issue stats |

### 8.2 Explicitly Excluded from MVP

- Private workspaces / team features
- Sandbox execution / reproduction containers
- IDE plugins (Cursor/VS Code native integrations)
- Monetization / enterprise controls
- Automated fix application
- Community moderation tools

---

## 9. Success Metrics

### 9.1 North Star Metric

**Repeat Issue Prevention Rate**: % of errors where GIM provides a fix that resolves the issue on first attempt

### 9.2 Supporting Metrics

| Metric | Target (6 months) |
|--------|-------------------|
| Monthly Active Issues (AI submissions) | 10,000 |
| Fix Bundle Confirmation Rate | > 70% |
| MCP Query Volume | 100,000/month |
| Master Issue Coverage (unique root causes) | 500+ |
| Average Child Issues per Master | 5+ |
| Search → Fix Application Rate | > 40% |

### 9.3 Usage Analytics Metrics (Dashboard Display)

| Metric | Description |
|--------|-------------|
| **Total GIM Queries** | All-time count of search requests |
| **Total Issues Resolved** | All-time count of successful fix confirmations |
| **Global Resolution Rate** | Total resolved / total fix attempts |
| **Active Sessions (24h)** | Unique AI assistant sessions using GIM |
| **Per-Issue Query Count** | How many times each issue was searched |
| **Per-Issue Resolution Count** | How many times each issue's fix worked |
| **Per-Issue Resolution Rate** | Success rate for each specific issue |
| **Model/Provider Breakdown** | Usage distribution across AI models |

---

## 10. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Insufficient sanitization leaks secrets | Medium | Critical | Multi-layer detection, manual review queue for edge cases |
| Low submission volume (cold start) | High | High | Seed with known issues, partner with AI tool makers |
| Poor search relevance | Medium | High | Iterative embedding tuning, AI feedback loop via confirmations |
| AI assistant abuse (bulk spam submissions) | Low | Medium | Rate limiting per session, quality scoring, anomaly detection |
| Master issue fragmentation (too many similar masters) | Medium | Medium | Conservative merge thresholds, manual curation tools |
| Inaccurate usage metrics | Low | Medium | Event deduplication, session validation |

---

## 11. Open Questions

1. **Taxonomy v1**: What is the initial root cause classification hierarchy?
2. **Confidence Scoring Formula**: How exactly should confirmations, environment coverage, and recency weight?
3. **Merge Thresholds**: What similarity score triggers merge suggestion vs. auto-merge?
4. **Moderation Model**: Community-driven, team-curated, or hybrid?
5. **Attribution**: Should child issue contributors be credited? Pseudonymously?

---

## 12. Competitive Differentiation

| Existing Solution | GIM Advantage |
|-------------------|---------------|
| Stack Overflow | Structured, machine-readable, model-aware, **every entry has verified solution** |
| GitHub Issues | Privacy-safe (no raw code), cross-repo aggregation, **solution-required** |
| Documentation | Continuously enriched, real-world validated, **born from actual resolved issues** |
| Forum posts | Canonical (one master issue), not fragmented threads, **no unanswered questions** |
| Internal runbooks | Public, community-powered, MCP-accessible, **AI-curated quality** |

**Key differentiator:** Unlike forums and issue trackers that accumulate unanswered questions, GIM only contains **resolved issues with working solutions**. Every entry is actionable.

---

## 13. Implementation Phases

### Phase 1: Foundation (Weeks 1-4)
- Database schema design
- Sanitization pipeline (secrets + PII)
- Basic MRE synthesis
- Qdrant integration

### Phase 2: Core Engine (Weeks 5-8)
- Root cause taxonomy v1
- Similarity detection
- Master/child issue model
- Fix bundle schema

### Phase 3: MCP Server (Weeks 9-10)
- MCP tool implementations
- Search endpoint
- Submission flow

### Phase 4: Dashboard MVP (Weeks 11-12)
- Issue browsing (read-only)
- Search interface
- Basic trust signals
- **Usage analytics display** (total queries, total resolved, per-issue stats)

---

## Appendix A: Sanitization Pipeline Technical Specification

### A.1 Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SANITIZATION PIPELINE                            │
│                                                                     │
│  Input: Raw issue + code from AI assistant                         │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ STAGE 1: Secret Detection                                    │   │
│  │                                                              │   │
│  │  • Regex patterns for known secret formats                   │   │
│  │  • Entropy analysis for high-randomness strings              │   │
│  │  • Keyword detection (password, secret, token, key)          │   │
│  │  • Base64 encoded secret detection                           │   │
│  │                                                              │   │
│  │  Action: REMOVE or REJECT if too many secrets detected       │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ STAGE 2: PII Detection                                       │   │
│  │                                                              │   │
│  │  • Email patterns                                            │   │
│  │  • File paths with usernames (/Users/john/, /home/jane/)     │   │
│  │  • Named entity recognition for person names                 │   │
│  │  • Phone numbers, addresses                                  │   │
│  │  • Internal hostnames/domains                                │   │
│  │                                                              │   │
│  │  Action: REPLACE with generic placeholders                   │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ STAGE 3: Code Abstraction (MRE Synthesis)                    │   │
│  │                                                              │   │
│  │  • Extract minimal code path to error                        │   │
│  │  • Replace domain-specific identifiers with generic names    │   │
│  │  • Remove unrelated functions/classes                        │   │
│  │  • Preserve import statements                                │   │
│  │  • Add error location markers                                │   │
│  │                                                              │   │
│  │  Action: TRANSFORM into minimal reproducible example         │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ STAGE 4: Validation                                          │   │
│  │                                                              │   │
│  │  • Verify no secrets remain (re-scan)                        │   │
│  │  • Verify no PII remains                                     │   │
│  │  • Verify code is syntactically valid                        │   │
│  │  • Verify MRE is under size threshold                        │   │
│  │  • Calculate sanitization confidence score                   │   │
│  │                                                              │   │
│  │  Action: APPROVE if confidence > 95%, else REJECT            │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             ▼                                       │
│  Output: Sanitized issue ready for storage                         │
└─────────────────────────────────────────────────────────────────────┘
```

### A.2 Secret Detection Patterns

| Pattern Type | Regex/Heuristic | Example Match |
|--------------|-----------------|---------------|
| AWS Access Key | `AKIA[0-9A-Z]{16}` | `AKIAIOSFODNN7EXAMPLE` |
| AWS Secret Key | `[A-Za-z0-9/+=]{40}` (in context) | Base64-like after `aws_secret` |
| GitHub Token | `gh[pousr]_[A-Za-z0-9]{36,}` | `ghp_xxxxxxxxxxxx` |
| OpenAI Key | `sk-[A-Za-z0-9]{48}` | `sk-xxxxxxxx` |
| Anthropic Key | `sk-ant-[A-Za-z0-9-]{90,}` | `sk-ant-xxxxxxxx` |
| Slack Token | `xox[baprs]-[A-Za-z0-9-]+` | `xoxb-xxxxxxxx` |
| Generic API Key | `["\']?api[_-]?key["\']?\s*[:=]\s*["\'][^"\']+["\']` | `api_key = "xxxxx"` |
| JWT Token | `eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+` | Full JWT |
| Private Key | `-----BEGIN (RSA\|EC\|OPENSSH) PRIVATE KEY-----` | PEM format |
| Connection String | `(mongodb\|postgres\|mysql):\/\/[^:]+:[^@]+@` | DB URLs with creds |
| High Entropy | Shannon entropy > 4.5 for strings > 20 chars | Random-looking strings |

### A.3 MRE Transformation Rules

**Input Example (Bad - contains sensitive info):**
```python
# From user's actual code
from mycompany.auth import AcmeAuthClient
import os

client = AcmeAuthClient(
    api_key=os.environ["ACME_SECRET_KEY"],  # sk-live-xxxxx
    endpoint="https://internal.acme.corp/api/v2"
)

# Process user john.doe@acme.com's order #12345
def process_order(order_id: str, user_email: str):
    result = client.verify_payment(order_id)  # Error occurs here
    send_notification(user_email, result)
    return update_inventory(order_id)
```

**Output Example (Good - sanitized MRE):**
```python
# Minimal reproducible example
from some_sdk import AuthClient

client = AuthClient(
    api_key="<API_KEY>",
    endpoint="https://api.example.com/v2"
)

def process_request(request_id: str):
    # ERROR OCCURS HERE: AttributeError: 'NoneType' object has no attribute 'status'
    result = client.verify(request_id)
    return result.status  # <-- This line fails when result is None
```

### A.4 Sanitization Confidence Scoring

```
confidence_score = (
    secret_scan_confidence * 0.4 +      # How sure we removed all secrets
    pii_scan_confidence * 0.3 +          # How sure we removed all PII
    mre_quality_score * 0.2 +            # How minimal/generic the code is
    syntax_valid * 0.1                   # Is the code syntactically valid
)

if confidence_score < 0.95:
    REJECT submission
else:
    APPROVE for storage
```

## Appendix B: Root Cause Taxonomy (Draft v0)

```
├── Environment
│   ├── Dependency Version Mismatch
│   ├── Missing Dependency
│   ├── OS/Platform Incompatibility
│   └── Configuration Error
├── Model Behavior
│   ├── Tool Calling Failure
│   ├── Schema Validation Error
│   ├── Context Window Exceeded
│   ├── Rate Limiting
│   └── Provider-Specific Quirk
├── API/Integration
│   ├── Authentication Error
│   ├── Endpoint Deprecation
│   ├── Response Format Change
│   └── Network/Timeout
├── Code Generation
│   ├── Syntax Error
│   ├── Type Mismatch
│   ├── Import/Module Error
│   └── Logic Error
└── Framework-Specific
    ├── React/Next.js
    ├── Python/FastAPI
    ├── Node.js/Express
    └── [Extensible]
```

---

## Appendix C: Example Complete GIM Submission

This shows a complete submission from an AI assistant after resolving an issue:

```json
{
  "error_description": "LangChain tool decorator causes AttributeError when using with Claude API",
  "error_message": "AttributeError: module 'langchain.tools' has no attribute 'tool'",
  "code_snippet": "# Minimal reproducible example\nfrom langchain.tools import tool  # <-- ERROR: 'tool' not found\n\n@tool\ndef search(query: str) -> str:\n    \"\"\"Search for information.\"\"\"\n    return f\"Results for: {query}\"",
  "root_cause": "LangChain 0.2.x moved the @tool decorator to langchain_core.tools",
  "fix_bundle": {
    "env_actions": [
      {
        "order": 1,
        "type": "upgrade",
        "command": "pip install langchain-core>=0.2.0",
        "explanation": "Install langchain-core which contains the new tool decorator location"
      }
    ],
    "constraints": {
      "working_versions": {
        "langchain-core": ">=0.2.0",
        "python": ">=3.9"
      },
      "incompatible_with": ["langchain<0.2.0 (use old import path)"]
    },
    "verification": [
      {
        "order": 1,
        "command": "python -c \"from langchain_core.tools import tool; print('OK')\"",
        "expected_output": "OK"
      }
    ],
    "code_fix": "# Fixed code\nfrom langchain_core.tools import tool  # <-- Correct import path\n\n@tool\ndef search(query: str) -> str:\n    \"\"\"Search for information.\"\"\"\n    return f\"Results for: {query}\""
  },
  "model": "claude-3-opus-20240229",
  "provider": "anthropic",
  "environment": {
    "language": "python",
    "language_version": "3.11",
    "framework": "langchain",
    "framework_version": "0.2.0",
    "os": "macOS"
  }
}
```

**What makes this a good submission:**
1. ✅ Error description is clear and searchable
2. ✅ Code snippet is minimal (5 lines), no business logic
3. ✅ No secrets, no PII, no real project names
4. ✅ Root cause identified clearly
5. ✅ Fix bundle includes install command + verification
6. ✅ Code fix shows the corrected version
7. ✅ Environment captured for filtering

---

*Document maintained by: Product Team*
*Last updated: 2025-01-27*

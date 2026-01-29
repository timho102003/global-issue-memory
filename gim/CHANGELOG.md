# GIM Changelog

## [Unreleased] - 2026-01-29

### Changed - Vector Storage Optimization

#### Refactor: Merge 3 Named Vectors into 1 Combined Vector with Scalar Quantization

**Breaking Change**: Qdrant collection schema has changed. Existing collections must be migrated using `scripts/migrate_vectors.py`.

**Embedding Service Changes** (`src/services/embedding_service.py`):
- **Added `SECTION_SEPARATOR` constant**: `"\n---\n"` used to join sections
- **New `generate_combined_embedding()`**: Replaces `generate_issue_embeddings()`
  - Concatenates `error_message + root_cause + fix_summary` with separator
  - Returns single 3072-dim vector instead of 3 separate vectors
- **New `generate_search_embedding()`**: Wraps error-only queries in section structure
  - Ensures query and stored vectors share same semantic space
  - Format: `error_message + "" + ""` with separators

**Qdrant Client Changes** (`src/db/qdrant_client.py`):
- **Collection schema**: Single vector with INT8 scalar quantization
  - `quantization_config`: INT8 scalar, quantile=0.99, always_ram=True
  - 4x memory reduction while maintaining search quality
- **`upsert_issue_vectors()`**: Now takes single `vector` param instead of 3
- **`search_similar_issues()`**:
  - Removed `vector_name` parameter (no longer needed)
  - Changed default `score_threshold` from 0.5 to 0.2 (broader matching)
  - Changed default `limit` from 5 to 10 (more results)
  - Added quantization re-scoring with `oversampling=2.0` for precision

**Tool Updates**:
- `gim_search_issues.py`: Uses `generate_search_embedding()`
- `gim_submit_issue.py`: Uses `generate_combined_embedding()`

**Migration Benefits**:
- **Simpler API**: 1 vector per issue instead of 3 named vectors
- **Memory efficiency**: 4x reduction via INT8 quantization
- **Fast search**: Quantized vectors kept in RAM (no disk I/O)
- **High precision**: Re-scoring with oversampling maintains quality
- **Semantic alignment**: Query and storage use same section structure

#### New Migration Script

**Added `scripts/migrate_vectors.py`**:
- Fetches all master_issues from Supabase with fix summaries
- Drops old Qdrant collection
- Recreates collection with new single-vector schema
- Re-generates combined embeddings for all issues
- Upserts with new payload structure
- Supports `--dry-run` flag for preview

**Usage**:
```bash
# Preview migration
python -m scripts.migrate_vectors --dry-run

# Run migration
python -m scripts.migrate_vectors
```

**Test Coverage**: `tests/test_scripts/test_migrate_vectors.py`

### Changed - Configuration

#### JWT Token TTL Increase

**Configuration Change** (`src/config.py`):
- `access_token_ttl_hours` default changed from 1 to 24 hours
- Reduces token refresh frequency for better UX
- Still configurable via environment variable

## [Unreleased] - 2026-01-27

### Added - Infrastructure Improvements (Phases 1-4)

#### Phase 1: Logging Infrastructure
- **Custom Exception Hierarchy** (`src/exceptions.py`)
  - `GIMError`: Base exception with structured error details
  - `SupabaseError`: Database operation errors with table/operation context
  - `QdrantError`: Vector database errors with collection/operation context
  - `EmbeddingError`: Embedding generation errors with text length/model context
  - `SanitizationError`: Content sanitization errors with stage/content type context
  - `ValidationError`: Input validation errors with field/constraint context
  - All exceptions support error chaining and structured details

- **Centralized Logging** (`src/logging_config.py`)
  - Request context tracking via `ContextVar` for request tracing
  - `@log_operation` decorator for automatic operation timing and logging
  - `RequestContextFilter` for adding request IDs to all log records
  - Structured log format: `timestamp | level | logger | [request_id] | message`
  - Functions: `configure_logging()`, `get_logger()`, `set_request_context()`, etc.

#### Phase 2: Database Layer Error Handling
- **Supabase Client Improvements** (`src/db/supabase_client.py`)
  - Thread-safe singleton pattern with double-checked locking
  - Comprehensive try/except blocks with `SupabaseError`
  - Operation logging with request context
  - Structured error messages with table and operation details

- **Qdrant Client Improvements** (`src/db/qdrant_client.py`)
  - Thread-safe singleton pattern with double-checked locking
  - Comprehensive try/except blocks with `QdrantError`
  - Operation logging with request context
  - Structured error messages with collection and operation details
  - Auto-creation of collections with proper error handling

#### Phase 3: Child Issue Fields & Services
- **Contribution Type Classifier** (`src/services/contribution_classifier.py`)
  - Classifies child issue contributions into types:
    - `VALIDATION`: Confirms fix works
    - `ENVIRONMENT`: Environment-specific solution
    - `MODEL_QUIRK`: Model-specific behavior
    - `SYMPTOM`: New error variation (default)
  - Keyword-based classification with priority logic
  - Comprehensive logging of classification decisions

- **Environment Extractor** (`src/services/environment_extractor.py`)
  - Extracts environment information from submission context
  - Regex-based extraction of:
    - Language version (e.g., "Python 3.12.1", "Node.js 20.10.0")
    - Framework version (e.g., "FastAPI 0.104.1", "React 18.2.0")
    - Operating system (e.g., "macOS 14.5", "Ubuntu 22.04")

- **Model Behavior Parser** (`src/services/model_parser.py`)
  - Parses and validates model behavior information
  - Extracts model name and provider
  - Standardizes model naming conventions
  - Validates model-specific metadata

- **Enhanced Child Issue Fields**
  - Added to `gim_submit_issue` tool:
    - `language_version`: Programming language version
    - `framework_version`: Framework version used
    - `os`: Operating system
    - `model_behavior_notes`: List of model-specific behavior observations
    - `validation_success`: Whether the fix was validated
    - `validation_notes`: Notes about validation process

#### Phase 4: Error Handling in All Tools
- **Updated All Tool Files** with:
  - Try/except blocks using custom exceptions
  - Structured error handling and logging
  - Security hardening: Generic error messages for unexpected exceptions
  - Request context tracking throughout operation flow
  - Proper error propagation with context preservation

### Tests Added
- `tests/test_exceptions.py`: Custom exception hierarchy tests
- `tests/test_logging.py`: Logging infrastructure tests
- `tests/test_services/test_contribution_classifier.py`: Contribution classification tests
- `tests/test_services/test_environment_extractor.py`: Environment extraction tests
- `tests/test_services/test_model_parser.py`: Model parsing tests

### Security
- **Generic Error Messages**: Unexpected exceptions return generic messages to prevent information leakage
- **Structured Error Context**: Error details captured internally but not exposed in production
- **No Sensitive Data in Logs**: PII and secrets are never logged
- **Thread-Safe Operations**: Database clients use proper locking mechanisms

### Documentation
- Updated `README.md` (project root) with infrastructure improvements
- Updated `gim/README.md` with detailed recent improvements section
- Updated `docs/ROADMAP.md` with completed Phase 2 infrastructure tasks
- Updated `gim/docs/ARCHITECTURE.md`:
  - Added custom exception hierarchy section
  - Added centralized logging infrastructure section
  - Added contribution classification, environment extraction, and model parsing sections
  - Enhanced error handling documentation
- Updated `gim/docs/CONFIGURATION.md` with detailed logging configuration
- Updated `gim/docs/DATABASE.md` with database client improvements
- Created `gim/CHANGELOG.md` (this file)

### Changed
- All database operations now use structured exceptions instead of generic errors
- All tools now have comprehensive error handling and logging
- Database clients upgraded from simple wrappers to production-ready implementations
- Child issue submissions now capture richer metadata for better issue organization

### Performance
- Thread-safe singleton patterns prevent redundant client initialization
- Operation timing automatically logged for performance monitoring
- Request context tracking enables efficient debugging and tracing

## Previous Versions

### [0.1.0] - 2026-01-20 (Phase 1 Complete)
- Initial data models (MasterIssue, ChildIssue, FixBundle, etc.)
- Two-layer sanitization pipeline
- Database clients (Supabase, Qdrant)
- Embedding service (Google Gemini)
- MCP server with 5 tools defined
- OAuth 2.1 with PKCE authentication
- Comprehensive test suite (~75% coverage)

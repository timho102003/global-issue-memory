# GIM Setup & Configuration Guide

This guide walks you through setting up a local development environment for Global Issue Memory (GIM).

## Prerequisites

- **Python 3.12+** (required)
- **Git** (for cloning the repository)
- **Supabase account** (free tier available)
- **Qdrant** (local Docker or cloud instance)
- **Google Cloud account** (for Gemini API)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/gim.git
cd gim
```

### 2. Create Virtual Environment

```bash
# Navigate to the gim project directory
cd gim/

# Create virtual environment
python3.12 -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install core dependencies
pip install -e .

# Install development dependencies (includes pytest)
pip install -e ".[dev]"
```

### 4. Set Up External Services

#### Supabase (PostgreSQL)

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Create a new project
3. Note your project URL and API key (anon/public key)

**Important:** Database schema is not yet created. This will be added in Phase 1.

#### Qdrant (Vector Database)

**Option A: Local Docker (Recommended for Development)**

```bash
# Pull Qdrant Docker image
docker pull qdrant/qdrant

# Run Qdrant container
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant
```

Your Qdrant instance will be available at `http://localhost:6333`.

**Option B: Qdrant Cloud**

1. Go to [cloud.qdrant.io](https://cloud.qdrant.io)
2. Create a free cluster
3. Note your cluster URL and API key

#### Google Gemini API

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Note your API key

### 5. Configure Environment Variables

Create a `.env` file in the `gim/` directory:

```bash
# Copy example file
cp .env.example .env

# Edit with your credentials
nano .env  # or use your preferred editor
```

**Required Environment Variables:**

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-qdrant-api-key  # Leave empty for local Docker

# Google AI Configuration
GOOGLE_API_KEY=your-google-api-key

# Optional: Model Configuration
EMBEDDING_MODEL=text-embedding-004
LLM_MODEL=gemini-2.5-flash-preview-05-20

# Optional: Logging
LOG_LEVEL=INFO
```

### 6. Verify Installation

```bash
# Run tests
pytest -v

# Expected output:
# tests/test_models/test_issue.py::test_master_issue_validation PASSED
# tests/test_models/test_environment.py::test_model_info_validation PASSED
# ...
# ==================== XX passed in X.XXs ====================
```

## Running the MCP Server

### Start the Server

```bash
# Make sure you're in the gim/ directory with .venv activated
python main.py
```

The server will start and listen for MCP protocol messages on stdio.

### Configure Claude Desktop (or other MCP client)

Add GIM to your MCP client configuration:

**For Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`):**

```json
{
  "mcpServers": {
    "gim": {
      "command": "python",
      "args": ["/absolute/path/to/gim/main.py"],
      "env": {
        "SUPABASE_URL": "https://your-project.supabase.co",
        "SUPABASE_KEY": "your-supabase-key",
        "QDRANT_URL": "http://localhost:6333",
        "QDRANT_API_KEY": "",
        "GOOGLE_API_KEY": "your-google-api-key"
      }
    }
  }
}
```

**Important:** Use absolute paths in MCP configurations.

### Verify MCP Tools are Available

In your MCP client (e.g., Claude Desktop), you should see 5 GIM tools:

- `gim_search_issues`
- `gim_get_fix_bundle`
- `gim_submit_issue`
- `gim_confirm_fix`
- `gim_report_usage`

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest -v

# Run specific test file
pytest tests/test_models/test_issue.py -v

# Run with coverage
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Code Quality

```bash
# Format code (if using black)
black src/ tests/

# Type checking (if using mypy)
mypy src/

# Linting (if using ruff)
ruff check src/ tests/
```

### Debugging

**Enable debug logging:**

```bash
# In .env
LOG_LEVEL=DEBUG
```

**Check logs:**

The MCP server logs to stderr. Redirect to a file for easier debugging:

```bash
python main.py 2> gim_debug.log
```

## Database Setup (Phase 1 - Coming Soon)

Once the database schema is implemented, you'll need to run migrations:

```bash
# Planned commands (not yet implemented)
python scripts/init_db.py
python scripts/run_migrations.py
```

**Manual Setup (Temporary):**

For now, you can manually create tables in Supabase Studio:

1. Go to your Supabase project
2. Navigate to SQL Editor
3. Run the SQL schema from `docs/ARCHITECTURE.md` (see Database Layer section)

## Qdrant Collection Setup

The MCP server automatically creates the Qdrant collection on startup. You can verify it:

```bash
# Check collections
curl http://localhost:6333/collections

# Expected response:
{
  "result": {
    "collections": [
      {"name": "gim_issues"}
    ]
  }
}
```

## Troubleshooting

### Issue: "Module 'mcp' not found"

**Solution:**
```bash
# Ensure you're in the virtual environment
source .venv/bin/activate

# Reinstall dependencies
pip install -e ".[dev]"
```

### Issue: "Connection refused to Qdrant"

**Solution:**
```bash
# Check if Qdrant is running
docker ps | grep qdrant

# If not running, start it
docker run -p 6333:6333 qdrant/qdrant

# Or check your QDRANT_URL in .env
```

### Issue: "Google API authentication failed"

**Solution:**
```bash
# Verify your API key
curl -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"test"}]}]}' \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=YOUR_API_KEY"

# If failed, regenerate key at https://makersuite.google.com/app/apikey
```

### Issue: "Supabase connection timeout"

**Solution:**
- Check your SUPABASE_URL (should include `https://`)
- Verify your API key is the "anon" key, not the "service_role" key
- Check your internet connection
- Verify your Supabase project is not paused (free tier pauses after inactivity)

### Issue: Tests failing with "ModuleNotFoundError"

**Solution:**
```bash
# Ensure you installed the package in editable mode
pip install -e .

# Verify package is installed
pip show gim
```

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SUPABASE_URL` | Yes | - | Supabase project URL |
| `SUPABASE_KEY` | Yes | - | Supabase anon/public key |
| `QDRANT_URL` | Yes | - | Qdrant instance URL |
| `QDRANT_API_KEY` | No | - | Qdrant API key (empty for local) |
| `GOOGLE_API_KEY` | Yes | - | Google AI Studio API key |
| `EMBEDDING_MODEL` | No | `gemini-embedding-001` | Google embedding model |
| `LLM_MODEL` | No | `gemingemini-3-flash-preview` | Google LLM model for sanitization |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Next Steps

- Read the [Architecture Guide](ARCHITECTURE.md) to understand system design
- Read the [API Reference](API.md) to learn about MCP tools
- Read the [PRD](PRD_Global_Issue_Memory.md) for full product specification
- Check the [Contributing Guide](CONTRIBUTING.md) for development guidelines

## Getting Help

- Check existing [GitHub Issues](https://github.com/your-org/gim/issues)
- Read the [FAQ](FAQ.md) (coming soon)
- Join the [Discord community](https://discord.gg/gim) (coming soon)

## Docker Setup (Alternative)

**Coming Soon:** Docker Compose setup for one-command local environment.

```bash
# Planned for Phase 2
docker-compose up
```

This will spin up:
- GIM MCP server
- Qdrant
- PostgreSQL (local alternative to Supabase)
- Dashboard UI (when implemented)

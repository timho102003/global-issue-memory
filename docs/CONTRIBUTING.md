# Contributing to GIM

Thank you for your interest in contributing to Global Issue Memory (GIM)! This guide will help you get started.

## Development Philosophy

GIM follows Test-Driven Development (TDD) and emphasizes:

- **Privacy First** - All submissions must be sanitized
- **Quality Over Quantity** - Every issue must include a verified solution
- **AI-First Design** - Tools are optimized for AI assistant usage
- **Clear Documentation** - Code should be self-documenting with good docstrings

## Getting Started

### 1. Fork and Clone

```bash
git clone https://github.com/your-username/gim.git
cd gim
git remote add upstream https://github.com/original-org/gim.git
```

### 2. Set Up Development Environment

Follow the [Setup Guide](SETUP.md) to configure your local environment.

```bash
cd gim/
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/issue-number
```

## Development Workflow

### 1. Write Tests First

Before implementing any feature, write failing tests.

```python
# tests/test_feature/test_new_feature.py
import pytest
from src.services.new_feature import new_function

def test_new_function_happy_path():
    """Test new_function with valid input."""
    result = new_function("valid_input")
    assert result == "expected_output"

def test_new_function_edge_case():
    """Test new_function with edge case."""
    with pytest.raises(ValueError):
        new_function("invalid_input")
```

Run tests to confirm they fail:

```bash
pytest tests/test_feature/test_new_feature.py -v
```

### 2. Implement Feature

Write minimal code to make tests pass.

```python
# src/services/new_feature.py
def new_function(input_data: str) -> str:
    """Do something with input_data.

    Args:
        input_data: The input string to process.

    Returns:
        str: The processed result.

    Raises:
        ValueError: If input_data is invalid.
    """
    if not input_data or input_data == "invalid_input":
        raise ValueError("Input data must be valid")

    return "expected_output"
```

### 3. Run Tests

```bash
# Run all tests
pytest -v

# Run specific test file
pytest tests/test_feature/test_new_feature.py -v

# Run with coverage
pytest --cov=src --cov-report=html
```

All tests must pass before submitting a PR.

### 4. Follow Code Standards

#### Python Standards

- **Docstrings** - Use Google style for all functions
- **Type Hints** - Always specify argument and return types
- **PEP 8** - Follow Python style conventions
- **Function Size** - Keep functions small and single-purpose
- **Variable Names** - Use descriptive names

**Example:**

```python
from typing import List, Optional
from pydantic import BaseModel

def sanitize_error_message(
    error: str,
    context: Optional[dict] = None
) -> str:
    """Sanitize an error message for public storage.

    This function removes secrets, PII, and sensitive paths from
    error messages before they are stored in the database.

    Args:
        error: The raw error message to sanitize.
        context: Optional context information for better sanitization.

    Returns:
        str: The sanitized error message.

    Raises:
        ValueError: If error is empty or None.

    Example:
        >>> sanitize_error_message("Error: API key sk-abc123 failed")
        "Error: API key <REDACTED> failed"
    """
    if not error:
        raise ValueError("Error message cannot be empty")

    # Implementation here
    return sanitized_error
```

#### Pydantic Models

- All API inputs/outputs must use Pydantic models
- All database writes must be validated through Pydantic first
- Use field validators for complex validation logic

```python
from pydantic import BaseModel, Field, field_validator

class SubmissionRequest(BaseModel):
    error_description: str = Field(..., min_length=10, max_length=5000)
    code_snippet: str = Field(..., min_length=5, max_length=10000)

    @field_validator('code_snippet')
    @classmethod
    def validate_code_snippet(cls, v: str) -> str:
        if 'sk-' in v or 'AKIA' in v:
            raise ValueError("Code snippet appears to contain secrets")
        return v
```

### 5. Database Operations

**Important:** Always ask user permission before:
- Writing data
- Deleting data
- Adding/modifying tables or schemas

```python
# In your PR description, include:
# "This PR requires database changes. Please review schema modifications in migration file."
```

Use Supabase MCP or direct client for database operations:

```python
from src.db.supabase_client import get_supabase_client

async def store_issue(issue: MasterIssue) -> UUID:
    """Store a new master issue."""
    client = get_supabase_client()

    result = await client.table("master_issues").insert(
        issue.model_dump(mode='json')
    ).execute()

    return result.data[0]['id']
```

### 6. Security Review

Before submitting, check your code against the security checklist:

- [ ] Input validation on all user/AI inputs
- [ ] No hardcoded secrets or API keys
- [ ] Sanitization applied before storage
- [ ] No sensitive info in error messages
- [ ] No PII in logs
- [ ] Environment variables for secrets

### 7. Documentation

Update relevant documentation:

- [ ] Code docstrings
- [ ] README.md (if adding major features)
- [ ] API.md (if adding/changing tools)
- [ ] ARCHITECTURE.md (if changing system design)

## Testing Guidelines

### Test File Naming

```
tests/
├── test_models/
│   ├── test_issue.py
│   ├── test_fix_bundle.py
│   └── test_environment.py
├── test_services/
│   ├── test_sanitization/
│   │   ├── test_secret_detector.py
│   │   ├── test_pii_scrubber.py
│   │   └── test_pipeline.py
│   └── test_embedding_service.py
└── test_tools/
    ├── test_search_issues.py
    └── test_submit_issue.py
```

### Test Function Naming

```python
def test_<function_name>_<scenario>():
    """Test description."""
    pass

# Examples:
def test_secret_detector_finds_api_keys():
    """Secret detector should identify API key patterns."""

def test_secret_detector_handles_empty_input():
    """Secret detector should handle empty string input."""

def test_secret_detector_ignores_safe_strings():
    """Secret detector should not flag safe strings as secrets."""
```

### Test Coverage

- Aim for >80% code coverage
- Cover happy path, edge cases, and error conditions
- Use pytest fixtures for common setup

```python
# conftest.py
import pytest
from src.models.issue import MasterIssue

@pytest.fixture
def sample_master_issue():
    """Fixture for a sample master issue."""
    return MasterIssue(
        id="550e8400-e29b-41d4-a716-446655440000",
        canonical_title="Test Issue",
        root_cause_category="Environment - Dependency Version Mismatch",
        # ... other fields
    )

# test_something.py
def test_function_with_issue(sample_master_issue):
    """Test function using the fixture."""
    result = process_issue(sample_master_issue)
    assert result is not None
```

## Pull Request Process

### 1. Update Your Branch

```bash
git fetch upstream
git rebase upstream/main
```

### 2. Run Full Test Suite

```bash
pytest -v
```

All tests must pass.

### 3. Commit Messages

Use conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `test`: Adding tests
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `chore`: Maintenance tasks

**Example:**

```
feat(sanitization): add entropy-based secret detection

- Implement Shannon entropy calculation
- Add threshold-based detection for high-entropy strings
- Add tests for various entropy levels

Closes #123
```

### 4. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Go to GitHub and create a Pull Request.

### 5. PR Template

```markdown
## Description
Brief description of what this PR does.

## Related Issue
Fixes #123

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Database Changes
- [ ] No database changes
- [ ] Database changes included (describe below)

## Security Review
- [ ] Input validation added
- [ ] Sanitization applied where needed
- [ ] No secrets in code
- [ ] Error messages don't leak sensitive info

## Documentation
- [ ] Code docstrings updated
- [ ] README updated (if needed)
- [ ] API docs updated (if needed)
```

### 6. Code Review

Your PR will be reviewed by maintainers. Be prepared to:

- Answer questions about design decisions
- Make changes based on feedback
- Rebase if requested

## Code Review Checklist

When reviewing PRs, check for:

- [ ] Tests pass and have good coverage
- [ ] Code follows style guidelines
- [ ] Docstrings are clear and complete
- [ ] No security vulnerabilities
- [ ] Database operations have permission
- [ ] Error handling is appropriate
- [ ] Performance is acceptable

## Development Tips

### Reuse Existing Functions

Before writing new code, check for existing utilities:

```bash
# Search for similar functions
rg "def sanitize" --type py
rg "class.*Client" --type py
```

**DRY Principle:** Don't Repeat Yourself. If you find duplicate logic, refactor into a shared utility.

### Use MCP Tools for Lookups

When you need library documentation or API references:

```bash
# Use context7 MCP for library questions
# Use supabase MCP for database operations
```

### Debugging

Enable debug logging:

```bash
# In .env
LOG_LEVEL=DEBUG
```

Use pytest debug mode:

```bash
pytest tests/test_file.py -v -s --pdb
```

### Performance Testing

For performance-critical code:

```python
import time

def test_sanitization_performance():
    """Sanitization should complete in <100ms."""
    start = time.time()

    result = sanitize_large_input(test_data)

    duration = time.time() - start
    assert duration < 0.1  # 100ms
```

## Common Pitfalls

### 1. Not Testing Edge Cases

```python
# Bad: Only tests happy path
def test_parse_version():
    assert parse_version("1.2.3") == (1, 2, 3)

# Good: Tests edge cases
def test_parse_version_edge_cases():
    assert parse_version("1.2.3") == (1, 2, 3)
    assert parse_version("1.0") == (1, 0, 0)
    with pytest.raises(ValueError):
        parse_version("invalid")
    with pytest.raises(ValueError):
        parse_version("")
```

### 2. Overfitting Prompts to Test Cases

When improving prompt-based features:

- **Don't:** Add specific examples just to pass failing tests
- **Do:** Improve core instruction clarity and generalize

### 3. Not Using Async/Await Properly

```python
# Bad: Blocking call in async function
async def fetch_data():
    result = requests.get(url)  # Blocks event loop!
    return result

# Good: Use async HTTP client
async def fetch_data():
    async with httpx.AsyncClient() as client:
        result = await client.get(url)
        return result
```

### 4. Not Validating with Pydantic

```python
# Bad: Direct database write
await db.table("issues").insert(raw_dict)

# Good: Validate through Pydantic first
issue = MasterIssue(**raw_dict)  # Validates types
await db.table("issues").insert(issue.model_dump())
```

## Getting Help

- **Documentation:** Check [docs/](../docs/) first
- **GitHub Issues:** Search existing issues or create a new one
- **Discord:** Join our community (link coming soon)
- **Code Examples:** Look at existing tests for patterns

## Recognition

Contributors are recognized in:

- GitHub Contributors list
- Project README (for significant contributions)
- Release notes (for features/fixes in releases)

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## Questions?

If you have questions about contributing:

1. Check existing documentation
2. Search GitHub issues
3. Open a new issue with the `question` label
4. Join our Discord community

Thank you for contributing to GIM!

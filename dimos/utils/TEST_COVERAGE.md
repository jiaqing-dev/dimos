# Utility Module Test Coverage

This document describes the test coverage for the dimos utility modules.

## Test Files

### test_colors.py
Tests for ANSI color formatting functions used in terminal output.

**Coverage:**
- All 6 color functions (green, blue, red, yellow, cyan, orange)
- Edge cases: empty strings, multiline text, special characters, unicode
- ANSI escape code validation

**Total Tests:** 10

### test_sequential_ids.py
Tests for the thread-safe sequential ID generator.

**Coverage:**
- Basic sequential increment behavior
- Multiple independent instances
- Thread safety with concurrent access (10 threads × 100 IDs)
- Concurrent barrier synchronization
- Large sequence generation (10,000 IDs)

**Total Tests:** 6

### test_constants.py
Tests for project-wide constants and configuration values.

**Coverage:**
- Project root path validation
- Log directory configuration
- Image capacity constants (color: 1920×1080×3, depth: 1280×720×4)
- LCM channel name length limits
- Project structure validation

**Total Tests:** 11

## Running Tests

### Run all utility tests:
```bash
DIMOS_SKIP_AUTOCONF=1 uv run pytest dimos/utils/test_*.py dimos/test_constants.py -v
```

### Run specific test file:
```bash
DIMOS_SKIP_AUTOCONF=1 uv run pytest dimos/utils/test_colors.py -v
```

### Run with coverage:
```bash
DIMOS_SKIP_AUTOCONF=1 uv run pytest dimos/utils/test_*.py --cov=dimos.utils --cov-report=html
```

## Test Configuration

The `DIMOS_SKIP_AUTOCONF` environment variable is used to skip system configuration checks during simple unit tests. This is configured in `dimos/conftest.py`.

A local `dimos/utils/conftest.py` provides additional test fixtures specific to utility module tests.

## Total Coverage

- **Total Tests:** 27
- **All tests passing:** ✓
- **Execution time:** ~0.03s

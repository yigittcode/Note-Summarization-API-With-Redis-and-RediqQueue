# Test Suite

Modern integration test suite for the AI Summarizer API.

## Features

- **Database Isolation**: Uses SQLite in-memory database for tests
- **Async Support**: Full async/await support with pytest-asyncio
- **Integration Tests**: End-to-end API testing
- **Role-Based Testing**: Tests ADMIN/AGENT permission levels
- **Docker Ready**: Runs in containerized environment

## Test Coverage

### Health & System Tests (`test_health.py`)
- API health checks
- Root endpoint validation

### User Authentication Tests (`test_users.py`)
- User registration (signup)
- User login/authentication
- Email validation
- Duplicate email handling

### Note Management Tests (`test_notes.py`)
- Note creation and retrieval
- Pagination and filtering
- Search functionality
- Role-based access control (ADMIN vs AGENT)

### Authentication & Security Tests (`test_auth.py`)
- JWT token validation
- Protected endpoint access
- Role-based authorization
- Token structure validation

## Running Tests

### Using Docker (Recommended)
```bash
# Run all tests
docker compose --profile test run --rm test

# Run specific test file
docker compose --profile test run --rm test pytest tests/test_users.py -v
```

### Using Test Runner Script
```bash
# Try Docker first, fallback to local
python3 run_tests.py

# Force local execution
python3 run_tests.py --local
```

### Direct pytest (requires dependencies)
```bash
pytest tests/ -v
```

## Test Configuration

- **pytest.ini/pyproject.toml**: Main test configuration
- **conftest.py**: Shared test fixtures and database setup
- **Test Database**: Uses `sqlite+aiosqlite:///./test.db` (isolated from production)

## Test Structure

```
tests/
├── __init__.py
├── conftest.py          # Fixtures and database setup
├── test_auth.py         # Authentication tests
├── test_health.py       # Health/system tests
├── test_notes.py        # Note management tests
└── test_users.py        # User registration/login tests
```

## Key Features

✅ **22 integration tests** covering all major functionality
✅ **Database isolation** - tests don't affect production data
✅ **Modern async/await** testing with proper fixtures
✅ **Role-based access** testing (ADMIN/AGENT permissions)
✅ **Docker containerized** testing environment
✅ **Simple but effective** - focuses on critical user journeys
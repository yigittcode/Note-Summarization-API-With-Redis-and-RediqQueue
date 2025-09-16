# 🚀 AI Summarizer API

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![Tests](https://img.shields.io/badge/Tests-35%20Passing-brightgreen.svg)](https://pytest.org)

A modern, production-ready **FastAPI application** with **JWT authentication**, **role-based access control**, and **asynchronous background processing** for AI-powered note summarization.

## ✨ Features

- **🔐 JWT Authentication** with role-based access (ADMIN/AGENT)
- **🤖 AI Background Processing** using Redis Queue for note summarization
- **📊 Advanced API** with pagination, filtering, and comprehensive docs
- **🏗️ Clean Architecture** with dependency injection and SOLID principles
- **🐳 Docker Ready** with multi-service orchestration
- **🧪 Comprehensive Testing** (35 tests with 100% critical path coverage)
- **📝 Production-Grade** error handling and logging

## 🚀 Quick Start

### 1. Clone & Start
```bash
git clone <your-repo-url>
cd ai-summarizer-api
docker compose up --build
```

### 2. Test the API
```bash
# Health check
curl http://localhost:8000/health

# View docs
open http://localhost:8000/docs
```

**📖 Full setup guide**: See [GETTING_STARTED.md](GETTING_STARTED.md)

## 🎬 Demo Flow

### 1. Create User
```bash
curl -X POST "http://localhost:8000/users/signup" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com", "password": "admin123", "role": "ADMIN"}'
```

### 2. Login & Get Token
```bash
curl -X POST "http://localhost:8000/users/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com", "password": "admin123"}'
```

### 3. Create Note (Auto-queues AI Summary)
```bash
curl -X POST "http://localhost:8000/notes/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"raw_text": "Important meeting about quarterly targets and strategy"}'
```

### 4. Check Status & Summary
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/notes/1"
```

## 🏗️ Architecture

### Tech Stack
- **Backend**: FastAPI (Python 3.11)
- **Database**: PostgreSQL with SQLAlchemy 2.0+ (async)
- **Queue**: Redis with RQ for background jobs
- **Auth**: JWT with bcrypt password hashing
- **Container**: Docker & Docker Compose

### Project Structure
```
ai-summarizer-api/
├── app/
│   ├── main.py              # FastAPI application
│   ├── models.py            # Database models
│   ├── core/               # Configuration, database, security
│   │   ├── config.py       # Settings management
│   │   ├── database.py     # Async database setup
│   │   ├── dependencies.py # Dependency injection
│   │   └── security.py     # JWT & password utilities
│   ├── users/              # User domain
│   │   ├── router.py       # User API endpoints
│   │   ├── service.py      # User business logic
│   │   ├── repository.py   # User data access
│   │   └── schema.py       # User Pydantic models
│   ├── notes/              # Notes domain
│   │   ├── router.py       # Note API endpoints
│   │   ├── service.py      # Note business logic
│   │   ├── repository.py   # Note data access
│   │   ├── schema.py       # Note Pydantic models
│   │   └── tasks.py        # Background job tasks
│   └── common/             # Shared utilities
│       ├── exceptions.py   # Custom exceptions
│       ├── pagination.py   # Pagination helpers
│       └── filtering.py    # Query filters
├── tests/                  # Test suite
├── alembic/               # Database migrations
├── docker-compose.yml     # Service orchestration
├── Dockerfile             # Container definition
└── requirements.txt       # Python dependencies
```

## 🧪 Testing

```bash
# Run all tests
docker compose --profile test run --rm test

# Run specific tests
docker compose --profile test run --rm test pytest tests/test_users.py -v
```

**Test Coverage:**
- 22 Integration tests (full API with database)
- 9 Unit tests (dependency injection with mocks)
- 4 Error handling tests (Redis failure scenarios)

## 🔧 Key Features

### Authentication & Authorization
- JWT tokens with configurable expiration
- Role-based access: **ADMIN** (sees all) vs **AGENT** (owns data)
- Secure password hashing with bcrypt

### Background Processing
- **Async job queuing** with Redis Queue (RQ)
- **AI-like summarization** based on content analysis
- **Status tracking**: `queued` → `processing` → `done`/`failed`

### API Features
- **Pagination** with metadata (page, size, total, pages)
- **Advanced filtering** (search, status, date ranges)
- **Comprehensive docs** with OpenAPI/Swagger
- **Robust error handling** with structured responses

### Production Ready
- **Dependency injection** for testability
- **Comprehensive logging** with error tracking
- **Docker containerization** with multi-service setup
- **Database migrations** with Alembic
- **Environment configuration** with Pydantic Settings

## 📊 API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/health` | Health check | ❌ |
| `POST` | `/users/signup` | User registration | ❌ |
| `POST` | `/users/login` | User authentication | ❌ |
| `POST` | `/notes/` | Create note (queues AI job) | ✅ |
| `GET` | `/notes/{id}` | Get note with status/summary | ✅ |
| `GET` | `/notes/` | List notes (paginated, filtered) | ✅ |

## 🏆 Assignment Requirements ✅

- ✅ **Auth & Tenancy**: JWT with ADMIN/AGENT roles
- ✅ **Models**: Users and notes with proper relationships
- ✅ **Async "AI summarize"**: Background jobs with status tracking
- ✅ **Dockerization**: Multi-service Docker Compose setup
- ✅ **Bonus Features**: Pagination, filtering, comprehensive testing

## 🎯 Advanced Implementation

### Dependency Injection
```python
class UserService:
    def __init__(self, user_repository: UserRepositoryInterface):
        self.repository = user_repository  # Injected dependency
```

### Error Handling
```python
except Exception as e:
    logger.error(f"Failed to enqueue job for note {note.id}: {e}", exc_info=True)
    await self.repository.update_note_status(note.id, NoteStatus.failed)
```

### Background Processing
```python
def summarize_note_task(note_id: int):
    # AI-like logic based on content analysis
    if "important" in text or "urgent" in text:
        summary = f"Priority summary: {text[:100]}..."
```


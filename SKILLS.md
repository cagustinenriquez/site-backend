# Project Skills & Conventions

Documentation for development practices, patterns, and conventions in this project.

## Quick Start

```bash
# One-command setup
make setup

# Run development server
make run

# Run tests
make test
```

## Project Structure

```
site-backend/
├── main.py              # FastAPI application entry point
├── app/
│   ├── __init__.py
│   ├── config.py        # Pydantic configuration/settings
│   ├── models.py        # Pydantic models (request/response schemas)
│   ├── crud.py          # Data operations (Create, Read, Update, Delete)
│   ├── auth.py          # Authentication & security (JWT, password hashing)
│   └── routes/
│       ├── __init__.py
│       ├── auth.py      # Authentication endpoints
│       └── posts.py     # Blog post endpoints
├── tests/
│   ├── __init__.py
│   └── test_api.py      # API endpoint tests
├── data/
│   └── posts.json       # File-based data storage (JSON)
├── Makefile             # Common development tasks
├── pyproject.toml       # Project metadata & dependencies (modern Python)
├── requirements.txt     # Python dependencies (pip-compatible)
└── .env                 # Environment configuration (DO NOT COMMIT)
```

## Development Workflow

### Installation

**First time setup:**
```bash
make setup
```

**Update dependencies:**
```bash
make install-dev
```

### Running the Server

```bash
make run
```

Then visit:
- **API Documentation**: http://localhost:8000/docs (interactive Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)
- **Health Check**: http://localhost:8000/health

### Testing

```bash
# Run all tests
make test

# Run tests matching a pattern
pytest -k "test_posts"

# Watch mode (reruns on file changes)
make test-watch
```

### Code Quality

```bash
# Check code style
make lint

# Auto-format code
make format
```

## Architecture Patterns

### 1. Routing & Endpoints

**Pattern:** Router-based organization with prefix and tags

```python
# routes/posts.py
from fastapi import APIRouter

router = APIRouter(prefix="/posts", tags=["posts"])

@router.get("")
async def list_posts(): ...
```

**Convention:**
- Prefix defines URL base (`/posts`, `/auth`)
- Tags group endpoints in documentation
- Each route file handles one resource
- Use async functions for all endpoints

### 2. Models & Validation

**Pattern:** Pydantic models for validation and serialization

```python
# models.py - Define models with clear inheritance
class PostBase(BaseModel):
    title: str
    content: str
    tags: List[str] = []

class PostCreate(PostBase):
    pass  # No additional fields needed

class Post(PostBase):
    id: str
    slug: str
    date: datetime
```

**Convention:**
- `*Base` - Shared fields
- `*Create` - Fields needed for creation
- `*Update` - Fields allowed for updates (all optional)
- `*Response` - Full response model (extends Base)
- Always use `from_attributes = True` in Config for ORM compatibility

### 3. CRUD Operations

**Pattern:** Centralized data operations in `crud.py`

```python
# crud.py
def create_post(post: PostCreate) -> Post: ...
def get_post(slug: str) -> Optional[Post]: ...
def list_posts(page: int = 1, limit: int = 10) -> tuple[List[Post], int]: ...
def update_post(slug: str, update: PostUpdate) -> Optional[Post]: ...
def delete_post(slug: str) -> bool: ...
```

**Convention:**
- Keep all data operations in `crud.py`
- Route files call CRUD functions, never access data directly
- Functions return domain models (Pydantic), not raw data
- Handle pagination internally (return tuple of items + total)

### 4. Authentication

**Pattern:** JWT-based token authentication

```python
# routes/posts.py
@router.post("")
async def create_post(
    post: PostCreate,
    current_user: str = Depends(get_current_user)  # Enforces auth
): ...
```

**Convention:**
- Use `Depends(get_current_user)` to protect endpoints
- GET/read endpoints: public
- POST/PUT/DELETE: require authentication
- Token expires after 30 minutes (set in `.env`)

### 5. Error Handling

**Pattern:** Use FastAPI's HTTPException for errors

```python
from fastapi import HTTPException

@router.get("/{slug}")
async def get_post(slug: str):
    post = crud.get_post(slug)
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    return post
```

**Convention:**
- 404 for not found
- 401 for unauthorized
- 403 for forbidden (authenticated but no permission)
- 422 for validation errors (automatic from Pydantic)

### 6. Configuration

**Pattern:** Environment variables via Pydantic Settings

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str = "default-key"
    debug: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()
```

**Convention:**
- Never hardcode secrets in code
- All config via `.env` or environment variables
- Use type hints for clarity
- Provide sensible defaults where appropriate

## Environment Variables

Required in `.env`:

```env
# Security (KEEP SECRET)
SECRET_KEY=your-super-secret-key-change-in-production
ADMIN_PASSWORD=admin

# App Settings
APP_NAME=agustinenriquez.dev API
DEBUG=true

# Database
DATABASE_URL=sqlite:///./blog.db

# Auth
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Important:** Never commit `.env` to git - it's in `.gitignore`

## API Conventions

### Request/Response Format

**Posts endpoints return:**
```json
{
  "id": "1",
  "slug": "post-title",
  "title": "Post Title",
  "content": "Full content...",
  "excerpt": "Short preview...",
  "tags": ["tag1", "tag2"],
  "date": "2026-08-30T12:00:00"
}
```

### Authentication

```bash
# 1. Get token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password": "admin"}'

# 2. Use token in requests
curl -X POST http://localhost:8000/posts \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "New Post", "content": "..."}'
```

### Pagination

```bash
# List with pagination
GET /posts?page=2&limit=20&tag=python

# Response includes metadata
{
  "posts": [...],
  "total": 42,
  "page": 2,
  "limit": 20
}
```

## Testing Strategy

**Test file:** `tests/test_api.py`

**Pattern:** Test each endpoint with success and failure cases

```python
def test_list_posts():
    """Happy path - list posts succeeds"""
    response = client.get("/posts")
    assert response.status_code == 200

def test_get_post_not_found():
    """Error case - post doesn't exist"""
    response = client.get("/posts/nonexistent")
    assert response.status_code == 404

def test_create_post_unauthorized():
    """Security - requires authentication"""
    response = client.post("/posts", json={...})
    assert response.status_code == 403
```

**Convention:**
- Test endpoint behavior, not internals
- Use descriptive test names
- Test both success and error cases
- Use `TestClient` from FastAPI for integration tests
- Run before commit: `make test`

## Common Tasks

### Add a New Endpoint

1. Update `app/models.py` if needed
2. Add CRUD function in `app/crud.py`
3. Add route in `app/routes/*.py`
4. Add test in `tests/test_api.py`
5. Run `make test` to verify

### Change Authentication

Edit `.env`:
```env
ADMIN_PASSWORD=your-new-password
SECRET_KEY=new-secret-key
```

Then restart the server.

### Work with Data

**View current data:**
```bash
cat data/posts.json
```

**Reset data:**
```bash
make clean-data
make init-data
```

## Known Issues & TODOs

- [ ] Password hashing needs proper bcrypt implementation (currently plaintext comparison)
- [ ] Rate limiting in API docs not actually enforced
- [ ] CORS allows all origins - restrict for production
- [ ] Error response format inconsistency between docs and code
- [ ] Consider switching from JSON to database for scalability

## Dependencies

### Core
- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **Python-jose** - JWT tokens
- **Passlib** - Password hashing

### Development
- **pytest** - Testing framework
- **httpx** - HTTP client for tests
- **pytest-asyncio** - Async test support

## Useful Make Commands

```bash
make help              # Show all available commands
make setup             # One-command full setup
make run               # Start dev server
make test              # Run tests
make format            # Auto-format code
make clean             # Remove cache/temp files
make clean-all         # Reset everything (keep git)
make init-data         # Create sample data
make docker-build      # Build Docker image
```

## Production Checklist

- [ ] Change `SECRET_KEY` in `.env`
- [ ] Change `ADMIN_PASSWORD` in `.env`
- [ ] Set `DEBUG=false`
- [ ] Set `CORS` allow_origins to specific domains
- [ ] Hash the admin password properly
- [ ] Review all TODOs in code
- [ ] Run full test suite
- [ ] Load test with expected traffic

## Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [JWT Basics](https://jwt.io/)
- [Local Development Guide](./GETTING_STARTED.md)
- [API Reference](./API.md)

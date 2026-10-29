# API Documentation

Base URL: `https://agustinenriquez.dev/api` (production) or `http://localhost:8000/api` (development)

## Authentication

Write operations (POST, PUT, DELETE) require JWT authentication.

### Getting a Token

1. Call the login endpoint with admin password:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'
```

2. Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

3. Use token in subsequent requests:
```bash
curl -X POST http://localhost:8000/posts \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "New Post", "content": "..."}'
```

Access tokens expire after 30 minutes; get a new one from `POST /auth/refresh` with the refresh token (valid 7 days). Reading blog posts doesn't require authentication; everything else does, including reading recruiters. Tokens stop working if their user is removed, and `admin` fallback tokens stop working once `data/users.json` has users.

## Endpoints

### Authentication

#### POST /auth/login
Get JWT access and refresh tokens

**Request Body:**
```json
{
  "username": "admin",
  "password": "admin"
}
```

Users are stored (argon2-hashed) in `data/users.json`; add one with
`uv run python scripts/create_user.py <username> <password>`. While that file
has no users, `admin` + `ADMIN_PASSWORD` is accepted instead. `username`
defaults to `admin` if omitted.

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### POST /auth/refresh
Swap a refresh token for a new access token and refresh token. Same rate limit as login.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** same shape as `/auth/login`. `401` if the refresh token is invalid or expired.

### Blog Posts

#### GET /posts
List all blog posts

**Query Parameters:**
- `page` (number) - Page number for pagination
- `limit` (number) - Results per page (default: 10)
- `tag` (string) - Filter by tag

**Response:**
```json
{
  "posts": [
    {
      "id": "post-1",
      "title": "Post Title",
      "slug": "post-slug",
      "excerpt": "Post excerpt...",
      "date": "2026-08-28T00:00:00Z",
      "tags": ["tag1", "tag2"]
    }
  ],
  "total": 42,
  "page": 1,
  "limit": 10
}
```

#### GET /posts/:slug
Get a single blog post

**Response:**
```json
{
  "id": "post-1",
  "title": "Post Title",
  "slug": "post-slug",
  "content": "Full post content...",
  "date": "2026-08-28T00:00:00Z",
  "tags": ["tag1", "tag2"]
}
```

#### POST /posts
Create a new blog post (requires authentication)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "title": "New Post",
  "content": "Post content...",
  "excerpt": "Optional excerpt",
  "tags": ["tag1"]
}
```

**Response:**
```json
{
  "id": "1",
  "slug": "new-post",
  "title": "New Post",
  "content": "Post content...",
  "excerpt": "Optional excerpt",
  "tags": ["tag1"],
  "date": "2026-08-28T12:00:00"
}
```

#### PUT /posts/{slug}
Update a blog post (requires authentication)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body (all fields optional):**
```json
{
  "title": "Updated Title",
  "content": "Updated content...",
  "excerpt": "Updated excerpt",
  "tags": ["updated"]
}
```

#### DELETE /posts/{slug}
Delete a blog post (requires authentication)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "detail": "Post deleted successfully"
}
```

### Recruiters

#### GET /recruiters (auth required)
List recruiters.

**Query Parameters:**
- `page` (number, default 1), `limit` (number, default 10, max 100)
- `sort` - `reputation` (default), `total_placements`, `average_rating` (highest first) or `name`
- `search` - case-insensitive match on name or company

**Response:**
```json
{
  "recruiters": [
    {
      "id": "1",
      "name": "Jane Doe",
      "company": "Acme",
      "email": "",
      "phone": null,
      "linkedin": null,
      "notes": "Great communication",
      "reputation": 3,
      "total_placements": 0,
      "average_rating": 0.0,
      "created_at": "2026-10-28T12:00:00",
      "updated_at": "2026-10-28T12:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 10
}
```

#### GET /recruiters/{id} (auth required)
Get one recruiter. `404` if not found.

#### POST /recruiters (auth required)
Body: `name` and `company` (required), plus optional `email`, `phone`, `linkedin`, `notes`, `reputation` (signed integer).

#### PUT /recruiters/{id} (auth required)
Any recruiter field, plus `total_placements` (>= 0) and `average_rating` (0-5). Only fields sent are changed.

#### DELETE /recruiters/{id} (auth required)

### Health Check

#### GET /health
Check API status

**Response:**
```json
{
  "status": "ok"
}
```

## Error Responses

All error responses follow this format:

```json
{
  "error": "Error message",
  "code": "ERROR_CODE"
}
```

### Common Error Codes

- `NOT_FOUND` - Resource not found
- `UNAUTHORIZED` - Missing or invalid authentication
- `FORBIDDEN` - Insufficient permissions
- `VALIDATION_ERROR` - Invalid request parameters
- `INTERNAL_ERROR` - Server error

## Rate Limiting

Requests are rate limited per client IP address:

| Endpoint | Limit |
|---|---|
| `POST /auth/login` | 5 requests per minute |
| `GET /health` | Not limited |
| All other endpoints | 100 requests per minute |

When a limit is exceeded the API returns `429 Too Many Requests`:

```json
{"error": "Rate limit exceeded: 5 per 1 minute"}
```

Limits are configurable with the `RATE_LIMIT_ENABLED`, `RATE_LIMIT_DEFAULT` and
`RATE_LIMIT_LOGIN` environment variables (see `.env.example`). Counters are kept
in memory, so each server process tracks its own limits.

## Versioning

The API uses URL versioning. Future versions will be at `/api/v2`, etc.

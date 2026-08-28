# API Documentation

Base URL: `https://agustinenriquez.dev/api` (production) or `http://localhost:8000/api` (development)

## Authentication

Write operations (POST, PUT, DELETE) require JWT authentication.

### Getting a Token

1. Call the login endpoint with admin password:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password": "admin"}'
```

2. Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
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

Token expires after 30 minutes. GET requests (read-only) don't require authentication.

## Endpoints

### Authentication

#### POST /auth/login
Get JWT access token

**Request Body:**
```json
{
  "password": "admin"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

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

API requests are limited to 100 requests per minute per IP address.

## Versioning

The API uses URL versioning. Future versions will be at `/api/v2`, etc.

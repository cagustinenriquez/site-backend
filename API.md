# API Documentation

Base URL: `https://agustinenriquez.dev/api` (production) or `http://localhost:3000/api` (development)

## Authentication

Add the following header to authenticated requests:
```
Authorization: Bearer <token>
```

## Endpoints

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
Create a new blog post (admin only)

**Request Body:**
```json
{
  "title": "New Post",
  "content": "Post content...",
  "tags": ["tag1"]
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

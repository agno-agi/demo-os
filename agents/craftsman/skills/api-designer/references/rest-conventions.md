# REST API Conventions

## Naming

- **Resources**: Plural nouns, lowercase, hyphen-separated — `/api/v1/user-profiles`
- **Actions**: Use HTTP methods, not verbs in URLs — `POST /orders` not `POST /create-order`
- **Sub-resources**: Nest under parent — `/users/:id/orders`
- **Query params**: snake_case — `?sort_by=created_at&order=desc`
- **Request/response fields**: camelCase in JSON — `{ "firstName": "Alice" }`

## Versioning

- **URL prefix**: `/api/v1/...` — increment major version for breaking changes
- **Breaking changes**: Removing fields, changing types, renaming endpoints
- **Non-breaking**: Adding optional fields, new endpoints, new query params
- **Deprecation**: Add `Sunset` header with removal date, document migration path

## HTTP Methods

| Method | Use | Idempotent | Body |
|--------|-----|------------|------|
| GET | Read resource(s) | Yes | No |
| POST | Create resource | No | Yes |
| PUT | Replace resource | Yes | Yes |
| PATCH | Partial update | No | Yes |
| DELETE | Remove resource | Yes | No |

## Status Codes

- **200** OK — successful GET, PUT, PATCH, DELETE
- **201** Created — successful POST
- **204** No Content — successful DELETE with no body
- **400** Bad Request — validation errors
- **401** Unauthorized — missing/invalid auth
- **403** Forbidden — insufficient permissions
- **404** Not Found — resource doesn't exist
- **409** Conflict — duplicate resource or state conflict
- **422** Unprocessable Entity — valid JSON but semantic errors
- **429** Too Many Requests — rate limit exceeded
- **500** Internal Server Error — unexpected failure

## Pagination

### Cursor-based (preferred)
```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6MTAwfQ==",
    "has_more": true
  }
}
```
Query: `?cursor=eyJpZCI6MTAwfQ==&limit=25`

### Offset-based
```json
{
  "data": [...],
  "pagination": {
    "total": 150,
    "offset": 0,
    "limit": 25
  }
}
```
Query: `?offset=0&limit=25`

## Error Response Format

```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "Validation failed",
    "details": [
      { "field": "email", "message": "Invalid email format" }
    ]
  }
}
```

## Filtering & Sorting

- **Filter**: `?status=active&role=admin`
- **Sort**: `?sort_by=created_at&order=desc`
- **Search**: `?q=search+term`
- **Fields**: `?fields=id,name,email` (sparse fieldsets)

## Rate Limiting

Return headers on every response:
- `X-RateLimit-Limit: 100`
- `X-RateLimit-Remaining: 87`
- `X-RateLimit-Reset: 1609459200`

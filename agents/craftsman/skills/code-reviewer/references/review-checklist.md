# Code Review Checklist

## Security
- [ ] No hardcoded secrets (API keys, passwords, tokens)
- [ ] SQL queries use parameterized statements
- [ ] User input is validated and sanitized
- [ ] Authentication and authorization checks are in place
- [ ] Sensitive data is not logged or exposed in error messages
- [ ] Dependencies are pinned and free of known vulnerabilities
- [ ] File uploads are validated (type, size, content)
- [ ] CORS and CSP headers are properly configured

## Correctness
- [ ] Edge cases are handled (empty input, null, zero, max values)
- [ ] Error handling catches specific exceptions
- [ ] Return types match function signatures
- [ ] Async/await is used consistently (no mixing sync/async)
- [ ] Database transactions have proper commit/rollback
- [ ] Race conditions are addressed in concurrent code
- [ ] Off-by-one errors in loops and slices

## Performance
- [ ] No N+1 query patterns
- [ ] Large collections use pagination or streaming
- [ ] Expensive operations are cached where appropriate
- [ ] Database queries use proper indexes
- [ ] No unnecessary object creation in hot paths
- [ ] Blocking I/O is not called from async context

## Maintainability
- [ ] Functions are under 30 lines
- [ ] Classes have a single responsibility
- [ ] Variable and function names are descriptive
- [ ] Complex logic has explanatory comments
- [ ] Magic numbers are replaced with named constants
- [ ] Duplicate code is extracted into shared functions
- [ ] Public APIs have docstrings

## Testing
- [ ] New code has corresponding tests
- [ ] Tests cover happy path and error cases
- [ ] Tests are deterministic (no flaky tests)
- [ ] Test names describe the scenario being tested
- [ ] Mocks are used sparingly and only at boundaries

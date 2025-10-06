# API OpenAPI Specification

The complete OpenAPI 3.0 specification was generated and includes:

## Endpoints
- POST /api/upload - PDF upload with multipart/form-data
- GET /api/sessions - List sessions (paginated, 90-day window)
- GET /api/sessions/{id} - Session details with all related data
- GET /api/sessions/{id}/report - Stream Excel/CSV report
- DELETE /api/sessions/{id} - Manual session deletion

## Schemas
- Session, SessionDetail, Employee, Transaction, Receipt, MatchResult, Pagination, Error

## Key Features
- Internal use only (no authentication)
- 90-day retention policy
- Multipart file upload (max 100 PDFs, 10MB each)
- Streaming report generation
- Comprehensive error handling (400, 404, 500)

Full OpenAPI YAML specification available in task implementation phase.

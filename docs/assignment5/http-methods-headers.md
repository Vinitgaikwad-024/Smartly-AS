# Assignment 5 — HTTP Methods and Headers

## Method/resource mapping
| Operation | Method + resource | Semantics / retry note |
|---|---|---|
| Search/read rooms | `GET /rooms`, `GET /rooms/{id}` | Safe, idempotent; filter and paginate lists |
| Create booking | `POST /bookings` | Not inherently idempotent; `Idempotency-Key` prevents duplicate creates for the same key |
| Read booking | `GET /bookings/{id}` | Safe; supports ETag / If-None-Match |
| Cancel/approve/reject | `POST /bookings/{id}/{transition}` | Explicit state transitions; repeated illegal transition returns 409 |
| Create room | `POST /admin/rooms` | 201 + Location |
| Update room | `PATCH /admin/rooms/{id}` | `If-Match` prevents stale writes; stale tag gives 412 |
| Delete room | `DELETE /admin/rooms/{id}` | 204 on success; 404 if already absent |
| Capabilities/preflight | `OPTIONS /...` | 204 + Allow and CORS headers |

## Header behavior
- `Content-Type`: JSON request body required for JSON writes; malformed JSON is 400, unsupported media type 415.
- `Accept`: JSON default; XML when explicitly requested; unsupported representation returns 406.
- `Authorization: Bearer ...`: required for booking/admin endpoints; absent/empty token returns 401 + `WWW-Authenticate`.
- `Location`: returned on create (201).
- `ETag`, `If-None-Match`: unchanged GET returns 304.
- `If-Match`: stale room update returns 412.
- `Idempotency-Key`: booking create replay returns the original resource and `Idempotency-Replayed: true`.
- `X-RateLimit-Limit`, `X-RateLimit-Remaining`: per-client sliding-window values for authenticated operations; 429 includes `Retry-After`.
- `X-Content-Type-Options: nosniff`; HSTS is enabled only when `SMARTLY_HTTPS_DEPLOYMENT=true` because HSTS should be served by HTTPS deployments.
- `OPTIONS` exposes `Allow`; CORS is permissive for coursework and must be restricted for a real deployment.

The rate limiter and store are in-memory and reset on process restart. This is suitable for a single-process demonstration, not a distributed production deployment. Run `bash scripts/capture-curl-transcript.sh` while the app is running to record real local responses.

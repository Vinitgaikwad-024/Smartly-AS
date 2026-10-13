# Smartly — Access Flow Control Management System

CS543 coursework project: campus room/lab search, booking requests, approvals and resource administration.

## Project layout
- `app.py`: Flask HTTP API.
- `models.py`: booking request validation contract.
- `store.py`: in-memory repository reference for the prototype (the current Flask app uses equivalent in-memory structures; this is not durable storage).
- `errors.py`: stable Problem Details type identifiers.
- `openapi.yaml`: OpenAPI 3.0.3 API contract.
- `database/schema.sql`: relational schema.
- `partner.wsdl`, `soap-*.xml`: design-time SOAP contract/envelopes for the fictional notification partner.
- `services/notification_client.py`: bounded retry/timeout outbound HTTP adapter.
- `tests/`: API and outbound-adapter tests.
- `docs/assignment1` through `docs/assignment6`: assignment reports/evidence notes.
- `docs/assignment2/*.drawio`, `*.svg`, `design.pdf`: editable and exported service/schema diagrams and design report.
- `docs/assignment3/integration.pdf`: SOAP integration report.
- `scripts/capture-curl-transcript.sh`: captures real local HTTP responses into `curl-transcript.txt`.

## Run locally (macOS/Linux)
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```
In another terminal, from this project root:
```bash
python -m pytest -q
bash scripts/capture-curl-transcript.sh
```
OpenAPI validation (install `openapi-spec-validator` in the same environment if needed):
```bash
python -m pip install openapi-spec-validator
openapi-spec-validator openapi.yaml
```

## Coursework limitations to disclose
- The API uses in-memory data and the demo token `local-demo`; this is not production authentication or durable storage.
- The SOAP partner and `.example.edu` endpoint are fictional; no live partner was called.
- The service diagram is a logical design; the current code is a single Flask prototype, not five deployed microservices.
- Browser DevTools measurements and public API captures must be recorded from the actual browser/network used for submission. Do not fabricate them or call local API traffic public API evidence.
- HSTS is emitted only when `SMARTLY_HTTPS_DEPLOYMENT=true`; serve the API behind HTTPS before enabling it.
- The rate limiter is process-local and resets when the app restarts.

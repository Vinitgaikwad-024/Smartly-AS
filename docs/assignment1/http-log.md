# Assignment 1 — HTTP by Hand

Run `python app.py`, then in another terminal run:

```bash
bash scripts/capture-curl-transcript.sh
```

This captures actual local `curl -i` requests/responses into root `curl-transcript.txt`. Review the output and summarize status codes and Content-Type here.

Required coverage includes at least five requests to the local Smartly API and one intentional 404. If the instructor strictly requires a public read-only JSON API, additionally run five `curl -i` requests against that public API and record those exact outputs separately; don't represent local Smartly calls as public API calls.
HTTP Request and Response Analysis

The HTTP requests were captured using curl -i. The transcript records the HTTP status line, response headers, and response body.
Evidence
Local API transcript: ../../curl-transcript.txt
Public API transcript: public-api-http-log.txt
Analysis
For each request, record the HTTP status code, Content-Type, and observed behavior. Include an intentional 404 response and explain how the API represents errors.

## Notes

- 200: successful read.
- 201: resource created; check `Location`.
- 304: cached representation is unchanged; no response body.
- 400/401/404/406/409/412/415/422: different client/request/resource/precondition failures.
- Error bodies should use `application/problem+json; charset=utf-8`.

TODO: paste/summarize actual captured output before submission.

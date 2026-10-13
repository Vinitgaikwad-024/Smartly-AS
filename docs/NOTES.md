# Smartly — CS543 shared submission notes

## Team

- Krity Kumari — 20252651030
- Ujjwal Sharma — 20252651060
- Vinit Gaikwad — 20252651019
- Shubhag Baluni — 20252651053

## Team Information

- Team ID: To be confirmed from the official course records.
- Krity Kumari — 20252651030
- Ujjwal Sharma — 20252651060
- Vinit Gaikwad — 20252651019
- Shubhag Baluni — 20252651053

Before submission, replace the Team ID placeholder with the
official assigned ID and verify all member details.

## Assignment continuity

This is one shared project. Assignments 1–3 establish the brief, service design, schema, and design-time SOAP integration. Assignments 4–6 extend the same REST API and tests; they are not separate duplicate APIs.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
# another terminal:
python -m pytest -q
```

## Important status

- Local Bearer token is for coursework demonstration only.
- SOAP endpoint is fictional; no live partner was contacted.
- Network measurements and HTTP transcripts must be captured from actual runs.
- Assignment 2 diagram sources/exports and Assignment 3 integration PDF are included.
- Validate OpenAPI with a validator and run the test suite in the local environment before submission.
- The notification adapter is a tested design example; the partner is fictional and is not called by the booking workflow.

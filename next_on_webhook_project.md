# Objective

Extend the existing ATS Integration module from a generic webhook receiver into a Workable Candidate Event Explorer.

The current implementation already supports:

* Receiving Workable webhooks
* API key validation
* Company validation
* Event persistence
* Event lookup
* HTML inspection pages

The next goal is to use a real Workable recruiter account and real candidate applications to collect candidate information through webhook events for testing and exploration purposes.

This phase is NOT about AI scoring.

This phase is ONLY about collecting, viewing, and inspecting candidate data received from Workable.

---

# Current State

Already implemented:

* POST /api/webhooks/workable
* Event storage in SQLite
* Event lookup API
* HTML event viewer
* API key authentication
* Integration validation
* Event queue placeholder

Do not remove or redesign these features.

Build on top of them.

---

# Goal

When a candidate applies to a Workable job:

1. Workable sends a webhook event.
2. The event is stored.
3. Candidate details are extracted and indexed.
4. Candidate details can be viewed from a browser.
5. Candidate details can be searched by:

   * Event ID
   * Candidate ID
   * Candidate Email
   * Job ID

The system should function as a Workable Event Inbox.

---

# New Database Fields

Extend WebhookEvent with optional extracted fields:

candidate_id
candidate_name
candidate_email
resume_url
job_id
job_title

These values should be extracted automatically from the payload when available.

The full payload must still be stored unchanged.

---

# Event Extraction Layer

Create a new service:

services.extract_candidate_details(payload)

Responsibilities:

* Detect candidate information
* Detect job information
* Handle missing fields safely
* Return structured data

Example output:

{
"candidate_id": "123",
"candidate_name": "John Doe",
"candidate_email": "[john@example.com](mailto:john@example.com)",
"resume_url": "https://...",
"job_id": "abc",
"job_title": "Backend Engineer"
}

This service should never fail if fields are missing.

---

# Candidate Search API

Add endpoint:

GET /api/candidates

Query Parameters:

candidate_id
email
job_id

Return matching events and extracted candidate information.

Example:

GET /api/candidates?candidate_id=123

Response:

{
"candidate_id": "123",
"name": "John Doe",
"email": "[john@example.com](mailto:john@example.com)",
"events": [...]
}

---

# Candidate Detail API

Add endpoint:

GET /api/candidates/{candidate_id}

Response:

{
"candidate_id": "123",
"name": "John Doe",
"email": "[john@example.com](mailto:john@example.com)",
"resume_url": "...",
"jobs": [...],
"events": [...]
}

---

# Event Inbox UI

Create:

GET /events

Display:

Event ID
Event Type
Candidate Name
Candidate Email
Job Title
Created At
Status

Newest events first.

Add pagination.

---

# Candidate Explorer UI

Create:

GET /candidates

Display:

Candidate Name
Email
Candidate ID
Latest Job Applied
Latest Event

Search box:

* Candidate ID
* Email

---

# Candidate Detail UI

Create:

GET /candidates/{candidate_id}

Display:

Candidate Name
Email
Candidate ID
Resume URL
Applied Jobs
Webhook Events

Include:

View Raw Payload

button

This should show the exact webhook payload stored in SQLite.

---

# Workable Testing Mode

Add a dedicated page:

GET /workable-test

Display:

Latest 20 webhook events.

For each event show:

* Event ID
* Event Type
* Candidate Name
* Candidate Email
* Resume URL
* Job Title
* Received Timestamp

This page exists purely for validating real Workable integrations.

---

# Resume Viewer

If resume_url exists:

Display:

Open Resume

button

which opens the resume URL in a new tab.

Do not download or parse the resume yet.

Only expose the URL.

---

# Logging

Add structured logging.

For every webhook received:

Log:

event_id
event_type
candidate_id
company_id

Example:

Received webhook:
event_id=evt_xxx
event_type=candidate_created
candidate_id=123
company_id=company_123

---

# Future Compatibility

Keep all candidate extraction logic separate from scoring logic.

The next phase will introduce:

* Resume parsing
* Skill extraction
* AI scoring
* Candidate ranking

The current implementation should be prepared for those features but must not implement them yet.

---

# Success Criteria

A recruiter can:

1. Post a test job in Workable.
2. Submit a test application.
3. Receive the webhook.
4. Obtain an event_id.
5. Search by event_id.
6. View candidate details.
7. View job details.
8. Open the resume URL.
9. Inspect the raw webhook payload.

No AI scoring is required for this phase.



Need to start implementation

# Implementation Decisions

## 1. Sample Workable Payload

A real Workable payload has not yet been captured.

For implementation purposes, do NOT hardcode assumptions about the payload structure.

Instead:

* Store the full raw payload exactly as received.
* Build a defensive extraction service.
* Allow candidate and job fields to be nullable.
* Treat the extraction layer as best-effort.

Example assumptions only:

{
"event": "candidate_created",
"data": {
"candidate": {
"id": "123",
"name": "John Doe",
"email": "[john@example.com](mailto:john@example.com)",
"resume_url": "https://..."
},
"job": {
"id": "job_123",
"title": "Backend Engineer"
}
}
}

However, implementation must not depend on this exact structure.

The actual payload will be discovered from live webhook testing.

---

## 2. Database Migration Strategy

Preserve the existing ats_integration.db database.

Do NOT recreate the database.

Additive schema changes only.

Preferred approach:

ALTER TABLE webhook_events
ADD COLUMN candidate_id TEXT;

ALTER TABLE webhook_events
ADD COLUMN candidate_name TEXT;

ALTER TABLE webhook_events
ADD COLUMN candidate_email TEXT;

ALTER TABLE webhook_events
ADD COLUMN resume_url TEXT;

ALTER TABLE webhook_events
ADD COLUMN job_id TEXT;

ALTER TABLE webhook_events
ADD COLUMN job_title TEXT;

Existing webhook events must remain intact.

Existing event_id values must remain valid.

---

## 3. Raw Payload Storage

The full raw webhook payload must always be stored exactly as received.

Requirements:

* No field removal.
* No field normalization.
* No field renaming.
* No transformation before persistence.

Store:

payload = request.json()

directly into the payload column.

Field extraction is a secondary operation.

The extracted fields are convenience indexes only.

The payload column remains the source of truth.

---

## 4. Pagination Strategy

Use simple offset/limit pagination.

Example:

GET /events?offset=0&limit=25

GET /events?offset=25&limit=25

Cursor pagination is unnecessary for this phase.

Keep implementation simple.

---

## 5. Schema Flexibility

Avoid strict webhook schemas.

The webhook payload structure may evolve.

Recommended approach:

* Accept payload as Dict[str, Any]
* Persist payload unchanged
* Extract known fields opportunistically

The webhook receiver should never reject a valid payload simply because a field moved location.

---

## 6. Extraction Service Requirements

Create:

services.extract_candidate_details(payload)

Return:

{
"candidate_id": null,
"candidate_name": null,
"candidate_email": null,
"resume_url": null,
"job_id": null,
"job_title": null
}

Populate values only when found.

Never raise exceptions.

Never fail webhook ingestion because extraction fails.

---

## 7. Event Processing Priority

Priority order:

1. Receive webhook
2. Store raw payload
3. Generate event_id
4. Persist event
5. Extract candidate/job metadata
6. Update indexed fields
7. Return 202 Accepted

Webhook ingestion must succeed even if extraction is incomplete.

---

## 8. Current Goal

The goal is not ATS integration.

The goal is not AI scoring.

The goal is not resume parsing.

The goal is to create a reliable Workable Event Inbox that allows:

* receiving real webhook events
* preserving raw payloads
* searching candidate information
* exploring event history
* validating Workable integrations

AI scoring will be implemented in a later phase.

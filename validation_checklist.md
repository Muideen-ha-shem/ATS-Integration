# Week 1 Validation Checklist

## Purpose

This checklist verifies that the implementation satisfies the Week 1 Workable Webhook Integration requirements.

Status Legend:

* [ ] Not Started
* [~] Partially Complete
* [x] Verified

---

# 1. Remove Development Artifacts

## Requirement

No dummy candidate data should remain in the active system.

### Validation

Search entire repository:

```bash
grep -R "Jane Doe" .
grep -R "John Doe" .
grep -R "company_123" .
grep -R "sk_test_company_123" .
```

### Expected

* No hardcoded candidate payloads in application code
* No webhook event seeding
* Test files may contain sample payloads only if isolated to tests

Status: [ ]

---

# 2. Configuration Management

## Requirement

Application configuration must come from environment variables.

### Validation

Check config.py

Verify:

```python
DATABASE_URL
APP_ENV
LOG_LEVEL
WORKABLE_API_TOKEN
```

are loaded from environment variables.

### Expected

No secrets hardcoded in source code.

Status: [ ]

---

# 3. Database Configuration

## Requirement

Database uses configuration settings.

### Validation

Inspect:

```text
src/app/database.py
```

Verify database path is not hardcoded.

Verify sample seeding is disabled by default.

### Expected

Application starts with no automatic candidate creation.

Status: [ ]

---

# 4. Webhook Receiver Endpoint

## Requirement

Application can receive Workable webhooks.

### Validation

Inspect route definitions.

Verify endpoint exists:

```http
POST /webhook/workable
```

or approved equivalent.

### Expected

Endpoint accepts JSON payloads.

Status: [ ]

---

# 5. Raw Payload Preservation

## Requirement

Webhook payload must be stored exactly as received.

### Validation

Submit test payload.

Retrieve stored payload.

Compare original payload with stored payload.

### Expected

No mutation of raw payload.

Status: [ ]

---

# 6. Candidate Metadata Extraction

## Requirement

Extract metadata without modifying payload.

### Validation

Send payload containing:

```json
{
  "candidate": {
    "id": "123",
    "name": "Jane Doe",
    "email": "jane@example.com"
  }
}
```

Verify extracted fields populate database columns.

### Expected

candidate_id populated

candidate_name populated

candidate_email populated

Status: [ ]

---

# 7. Event Storage

## Requirement

Webhook event is persisted.

### Validation

Trigger webhook.

Run:

```sql
SELECT COUNT(*)
FROM webhook_events;
```

### Expected

Count increases.

Status: [ ]

---

# 8. Event Retrieval API

## Requirement

Stored events can be retrieved.

### Validation

Retrieve:

```http
GET /events/{event_id}
```

### Expected

Stored payload returned.

Status: [ ]

---

# 9. Event Listing

## Requirement

Events can be browsed.

### Validation

Open:

```http
GET /events
```

### Expected

List of events displayed.

Status: [ ]

---

# 10. Logging

## Requirement

Lifecycle events are logged.

### Validation

Trigger webhook.

Verify logs show:

* webhook received
* webhook persisted
* processing status

### Expected

Structured logging present.

Status: [ ]

---

# 11. Sensitive Data Logging Review

## Requirement

Sensitive information should not be logged.

### Validation

Review logger statements.

Check for:

* resume content
* email addresses
* phone numbers

### Expected

No sensitive candidate data appears in logs.

Status: [ ]

---

# 12. Docker Build

## Requirement

Application runs inside Docker.

### Validation

Build image:

```bash
docker build -t workable-webhook .
```

### Expected

Build succeeds.

Status: [ ]

---

# 13. Docker Runtime

## Requirement

Container starts successfully.

### Validation

Run:

```bash
docker run -p 8000:8000 workable-webhook
```

### Expected

Application starts.

Status: [ ]

---

# 14. Health Endpoint

## Requirement

Application exposes health check.

### Validation

Call:

```http
GET /
```

or

```http
GET /health
```

### Expected

Returns status response.

Status: [ ]

---

# 15. Public Accessibility

## Requirement

Webhook endpoint can be reached externally.

### Validation

Deploy application.

Verify URL accessible.

### Expected

Public HTTPS endpoint available.

Status: [ ]

---

# 16. Workable Readiness

## Requirement

System is ready for real Workable integration.

### Validation

Confirm:

* public URL exists
* endpoint reachable
* payload persistence works
* logs working
* Docker image deployable

### Expected

Ready for webhook subscription creation.

Status: [ ]

---

# 17. Compliance Review

## Requirement

Basic compliance controls implemented.

### Validation

Verify:

* HTTPS enforced
* secrets stored in environment variables
* no secrets committed to Git
* raw payload access restricted

### Expected

Minimum compliance baseline achieved.

Status: [ ]

---

# 18. Definition of Done

The project is complete when all items above are verified and the first real Workable webhook is successfully stored.

Final Status:

[ ] Week 1 Complete

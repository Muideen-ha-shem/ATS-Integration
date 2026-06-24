# ATS Integration Implementation Summary

## Overview

This repository implements a FastAPI-based ATS webhook receiver with local persistence and a small inspection UI. It is designed to receive Workable webhook payloads, validate them with headers, store them in SQLite, and expose both JSON and HTML inspection endpoints.

## Main functionality

### Webhook ingestion

- Endpoint: `POST /api/webhooks/workable`
- Validates required headers:
  - `X-Api-Key`
  - `X-Company-Id`
- Verifies that a corresponding integration exists for the provided `company_id` and provider `workable`.
- Verifies the API key using SHA-256 hashed storage.
- Stores the incoming payload as a `WebhookEvent` record.
- Marks the event as queued via `services.queue_resume_for_scoring`.
- Returns `202 Accepted` with the created `event_id`.

### Event retrieval

- Endpoint: `GET /api/webhooks/workable/events/{event_id}`
  - Returns the stored webhook event as JSON.
  - Authentication is enforced using the same `X-Api-Key` and `X-Company-Id` headers.
  - Response uses `WebhookEventResponse` schema with timestamp fields.

- Endpoint: `GET /events/{event_id}`
  - Returns a rendered HTML page with event metadata and candidate resume details.
  - Requires the same headers for authentication.

### Browser inspection UI

- Endpoint: `GET /ui`
  - Displays a small HTML interface.
  - Lets the user enter `event_id`, `X-Api-Key`, and `X-Company-Id`.
  - Fetches `/api/webhooks/workable/events/{event_id}` and renders a summary plus raw JSON.

### Root health endpoint

- Endpoint: `GET /`
  - Responds with a simple JSON status message.

## Data model

### `Integration`

- `id`: integer primary key
- `company_id`: string
- `provider`: string (e.g. `workable`)
- `status`: string
- `callback_url`: optional string
- `created_at`: datetime

### `ApiKey`

- `id`: integer primary key
- `company_id`: string
- `key_hash`: SHA-256 hash of the API key
- `status`: string
- `expires_at`: optional datetime
- `created_at`: datetime

### `WebhookEvent`

- `event_id`: UUID string primary key
- `provider`: string
- `company_id`: string
- `event_type`: string
- `payload`: JSON
- `status`: string (`received`, later set to `queued`)
- `created_at`: datetime
- `queued_at`: optional datetime

## Validation schemas

### `CandidatePayload`

- `id`: string
- `name`: string
- `resume_url`: validated as `HttpUrl`

### `WebhookData`

- `candidate`: `CandidatePayload`

### `WorkableWebhookPayload`

- `event`: string
- `data`: `WebhookData`

### `WebhookEventResponse`

- `event_id`: string
- `provider`: string
- `company_id`: string
- `event_type`: string
- `payload`: dictionary
- `status`: string
- `created_at`: datetime
- `queued_at`: optional datetime

## Database and local setup

- Database file: `ats_integration.db` by default.
- Configured through `src/app/database.py`.
- Uses SQLite with `check_same_thread=False` for local runtime.
- Creates tables automatically on FastAPI startup.
- Seeds a sample integration and API key if they do not already exist:
  - `company_id`: `company_123`
  - `provider`: `workable`
  - `plain_key`: `sk_test_company_123`

## Authentication and authorization

- `X-Api-Key` is required on every protected endpoint.
- `X-Company-Id` is required on every protected endpoint.
- The API key is validated by hashing the provided key and comparing it to the stored `key_hash`.
- The company must have an active `Integration` configured for `workable`.

## Processing behavior

- Incoming webhook events are persisted using `crud.create_webhook_event`.
- After persistence, `services.queue_resume_for_scoring` updates the event:
  - sets `status` to `queued`
  - sets `queued_at` to the current UTC time
- This is currently a placeholder for a resume scoring pipeline.

## Support scripts

### `scripts/test_webhook.py`

- Uses `fastapi.testclient.TestClient`.
- Sends a sample `candidate_created` event to `/api/webhooks/workable`.
- Uses the seeded API key and company ID.
- Uses a transient test database `test_ats_integration.db`.

### `scripts/update_resume_urls.py`

- Connects directly to `ats_integration.db` using `sqlite3`.
- Reads records from `webhook_events`.
- Looks for candidate resume URLs and updates matching rows.
- Commits changes back into the SQLite database.

## Files touched

- `src/app/main.py`
- `src/app/schemas.py`
- `src/app/models.py`
- `src/app/crud.py`
- `src/app/database.py`
- `src/app/services.py`
- `scripts/test_webhook.py`
- `scripts/update_resume_urls.py`

## Current state summary

- Webhook receiver implemented
- Authentication and company/provider validation working
- Persistent storage of webhook payloads working
- Event inspection via API and HTML implemented
- Simple browser UI for event lookup implemented
- Resume URL patch script available

## Notes

- The app is currently configured for local development and demo usage.
- The resume scoring service is a stub; the event is only marked as `queued`.
- No callback or retry mechanism is implemented.

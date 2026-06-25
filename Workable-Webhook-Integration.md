# Workable Webhook Integration – Week 1 Implementation Plan

## Objective

Build a production-ready foundation for receiving candidate application events from Workable through webhooks, storing them securely, and preparing the platform for future resume parsing and AI scoring.

This phase focuses exclusively on:

* Receiving real Workable webhook events
* Secure storage of webhook payloads
* Candidate event inspection
* Deployment readiness
* Compliance and data protection

This phase does **not** include:

* Resume scoring
* Candidate ranking
* ATS workflow automation
* Production AI pipelines
* Multi-provider ATS integrations

---

# Target Architecture

```text
Workable
    │
    ▼
Webhook Subscription
    │
    ▼
Webhook Receiver API (FastAPI)
    │
    ▼
Webhook Processing Layer
    │
    ▼
Database Storage
    │
    ▼
Event Inspection UI
```

Future architecture:

```text
Workable
    │
    ▼
Webhook Receiver
    │
    ▼
Database
    │
    ▼
Resume Parser
    │
    ▼
AI Scoring Engine
    │
    ▼
ATS Platform
```

---

# Week 1 Deliverables

## Deliverable 1: Remove Development Artifacts

### Goal

Prepare the codebase for real webhook traffic.

### Tasks

* Remove all hardcoded candidate payloads
* Remove all "Jane Doe" test records
* Remove fake resume URLs
* Remove webhook event seeding
* Clean SQLite test data

### Validation

```sql
DELETE FROM webhook_events;
SELECT COUNT(*) FROM webhook_events;
```

Expected:

```text
0
```

---

# Deliverable 2: Build Dedicated Workable Webhook Receiver

### Goal

Receive and store real webhook events from Workable.

### Required Endpoints

#### Receive Webhook

```http
POST /webhook/workable
```

Responsibilities:

* Accept incoming JSON
* Validate payload structure
* Generate event identifier
* Store raw payload
* Log receipt
* Return success response

#### Event List

```http
GET /events
```

Responsibilities:

* Display received events
* Display event type
* Display received timestamp

#### Event Detail

```http
GET /events/{event_id}
```

Responsibilities:

* Display full raw payload
* Display extracted candidate metadata

---

# Deliverable 3: Database Design

### Goal

Preserve webhook data exactly as received.

### Webhook Event Table

```text
event_id
provider
event_type
payload
candidate_id
candidate_name
candidate_email
resume_url
job_id
job_title
status
received_at
```

### Requirements

* Store raw payload unchanged
* Preserve original webhook structure
* Support future replay and debugging

---

# Deliverable 4: Candidate Metadata Extraction

### Goal

Extract useful fields without modifying raw payloads.

### Extract

Candidate:

```text
candidate_id
candidate_name
candidate_email
resume_url
```

Job:

```text
job_id
job_title
```

### Requirements

* Extraction failures must not break ingestion
* Missing fields should default to null
* Raw payload remains authoritative source

---

# Deliverable 5: Dockerization

### Goal

Make the application deployable in Azure.

### Required Files

```text
Dockerfile
.dockerignore
requirements.txt
```

### Validation

Application must run using:

```bash
docker build -t workable-webhook .
docker run -p 8000:8000 workable-webhook
```

### Acceptance Criteria

Application starts successfully inside container.

---

# Deliverable 6: Configuration Management

### Goal

Remove hardcoded configuration.

### Required Environment Variables

```env
DATABASE_URL=
WORKABLE_API_TOKEN=
APP_ENV=
LOG_LEVEL=
```

### Rules

* No secrets in source code
* No secrets committed to Git
* Environment-specific configuration only

---

# Deliverable 7: Logging & Observability

### Goal

Support troubleshooting and operational monitoring.

### Log Events

Webhook received:

```text
provider
event_type
event_id
timestamp
```

Webhook persisted:

```text
event_id
status
```

Webhook errors:

```text
error_message
event_id
timestamp
```

### Requirements

* Structured logging
* No sensitive data in logs
* No resume contents logged

---

# Deliverable 8: Deployment Preparation

### Goal

Prepare for Azure development environment.

### Questions for Infrastructure Team

1. Azure Container Apps or App Service?
2. PostgreSQL availability?
3. Public HTTPS endpoint availability?
4. Secret management approach?
5. Logging and monitoring approach?

### Expected Deployment Flow

```text
GitHub
   │
   ▼
Azure Build
   │
   ▼
Docker Image
   │
   ▼
Azure Runtime
```

---

# Deliverable 9: Workable Integration Validation

### Goal

Prove end-to-end webhook functionality.

### Steps

1. Create Workable webhook subscription
2. Configure webhook target URL
3. Trigger candidate application
4. Confirm webhook delivery
5. Verify payload persistence
6. Verify event visibility in UI

### Success Criteria

A real Workable candidate application creates a corresponding event record.

---

# Deliverable 10: Compliance & Data Protection

## Data Classification

Candidate information should be treated as personal data.

Examples:

```text
Name
Email
Resume
Phone Number
Employment History
Education History
```

---

## Data Minimization

Store only information required for:

* Candidate evaluation
* Resume scoring
* Recruitment workflows

Do not collect unnecessary personal information.

---

## Secure Storage

Requirements:

* HTTPS only
* Encrypted database connections
* Secret management via environment variables
* No credentials in source control

---

## Logging Restrictions

Do not log:

```text
Resume contents
Email addresses
Phone numbers
Government IDs
Sensitive personal information
```

Log only operational metadata.

---

## Access Control

Requirements:

* Authentication for inspection endpoints
* Role-based access in future phases
* Principle of least privilege

---

## Retention Policy

Prepare retention strategy:

```text
Webhook events
Candidate resumes
Scoring results
Audit logs
```

Data should not be retained indefinitely without business justification.

---

## Auditability

Maintain:

```text
Webhook received timestamp
Event identifier
Processing status
Processing history
```

to support troubleshooting and compliance reviews.

---

# Out of Scope (Week 1)

The following are intentionally deferred:

* AI scoring
* Resume parsing
* Candidate ranking
* ATS integrations beyond Workable
* Background jobs
* Multi-tenancy
* Callback systems
* Notification systems
* Production analytics

---

# Definition of Done

The implementation is complete when:

* Real Workable webhook events are received
* Raw payloads are stored successfully
* Candidate metadata is extracted
* Events are viewable through UI/API
* Application runs in Docker
* Application is deployable to Azure
* Basic compliance controls are implemented
* No dummy candidate data remains in the system
* End-to-end testing with a real Workable candidate succeeds

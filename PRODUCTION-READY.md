# Production Ready Checklist

This file lists the production-readiness tasks for the ATS Integration project.

- [x] Confirm project type and language — FastAPI chosen.
- [x] Scaffold workspace skeleton (folders, .gitignore, license).
- [ ] Initialize git repository (optional).
- [x] Add sample source files and tests (basic code and test script added).
- [ ] Update README with run/test instructions (partial; can be expanded).
- [x] Test webhook endpoint (local tests pass, `scripts/test_webhook.py`).

Production-focused items to complete:

- [ ] Secure API key management and rotation: implement admin endpoints, use secret manager, enforce rotation.
- [ ] Use production-grade database and migrations: switch to Postgres, add Alembic migrations.
- [ ] Add persistent queue + worker for scoring: Redis/Celery or RQ worker, reliable retries.
- [ ] Implement idempotency and signature verification: provider event IDs, HMAC verification.
- [ ] Add callback delivery & retry logic: durable delivery, backoff, status tracking.
- [ ] Add logging, metrics, and TLS deployment: structured logging, Sentry, Prometheus, TLS termination.
- [ ] Add CI, tests, and integration tests: unit tests, integration tests with mock ATS.

Notes
- The webhook handler is in `src/app/main.py`.
- DB models and CRUD are in `src/app/models.py` and `src/app/crud.py`.
- Queue handoff stub is `src/app/services.py` — replace with real queue/worker.

Next recommended task: implement a queue publisher and worker (Redis + RQ/Celery) and add a migration setup (Alembic).

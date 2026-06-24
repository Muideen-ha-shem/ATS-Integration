"""CRUD helpers for integration, API key, and webhook event persistence."""

import hashlib
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app import models


def hash_api_key(api_key: str) -> str:
    """Create a SHA-256 hash from a plaintext API key."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def get_integration_by_company_and_provider(db: Session, company_id: str, provider: str) -> Optional[models.Integration]:
    """Return the integration record for a company and ATS provider."""
    return (
        db.query(models.Integration)
        .filter(models.Integration.company_id == company_id, models.Integration.provider == provider)
        .first()
    )


def get_api_key_for_company(db: Session, company_id: str) -> Optional[models.ApiKey]:
    """Return the active API key record for a company."""
    return db.query(models.ApiKey).filter(models.ApiKey.company_id == company_id, models.ApiKey.status == "active").first()


def validate_api_key(db: Session, company_id: str, api_key: str) -> bool:
    """Validate the provided API key against the stored hash."""
    stored = get_api_key_for_company(db, company_id)
    if not stored:
        return False
    return stored.key_hash == hash_api_key(api_key)


def create_integration(
    db: Session,
    company_id: str,
    provider: str,
    status: str = "active",
    callback_url: str | None = None,
) -> models.Integration:
    """Create and persist a new ATS integration record."""
    integration = models.Integration(
        company_id=company_id,
        provider=provider,
        status=status,
        callback_url=callback_url,
    )
    db.add(integration)
    db.commit()
    db.refresh(integration)
    return integration


def create_api_key(
    db: Session,
    company_id: str,
    plain_key: str,
    status: str = "active",
    expires_at: datetime | None = None,
) -> models.ApiKey:
    """Create and persist a new API key record for a company."""
    api_key = models.ApiKey(
        company_id=company_id,
        key_hash=hash_api_key(plain_key),
        status=status,
        expires_at=expires_at,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key


def create_webhook_event(
    db: Session,
    provider: str,
    company_id: str,
    event_type: str,
    payload: dict,
    status: str = "received",
) -> models.WebhookEvent:
    """Create and persist a new webhook event record."""
    event = models.WebhookEvent(
        provider=provider,
        company_id=company_id,
        event_type=event_type,
        payload=payload,
        status=status,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_webhook_event_by_id(db: Session, event_id: str) -> Optional[models.WebhookEvent]:
    """Return a webhook event by its unique identifier."""
    return db.query(models.WebhookEvent).filter(models.WebhookEvent.event_id == event_id).first()


def update_webhook_event_metadata(
    db: Session,
    event_id: str,
    candidate_id: str | None = None,
    candidate_name: str | None = None,
    candidate_email: str | None = None,
    resume_url: str | None = None,
    job_id: str | None = None,
    job_title: str | None = None,
) -> Optional[models.WebhookEvent]:
    """Update extracted candidate/job metadata for an existing webhook event."""
    event = get_webhook_event_by_id(db, event_id)
    if not event:
        return None

    if candidate_id is not None:
        event.candidate_id = candidate_id
    if candidate_name is not None:
        event.candidate_name = candidate_name
    if candidate_email is not None:
        event.candidate_email = candidate_email
    if resume_url is not None:
        event.resume_url = resume_url
    if job_id is not None:
        event.job_id = job_id
    if job_title is not None:
        event.job_title = job_title

    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def search_webhook_events(
    db: Session,
    candidate_id: str | None = None,
    email: str | None = None,
    job_id: str | None = None,
    limit: int = 25,
    offset: int = 0,
) -> list[models.WebhookEvent]:
    """Search webhook events by extracted candidate or job fields."""
    query = db.query(models.WebhookEvent)
    if candidate_id:
        query = query.filter(models.WebhookEvent.candidate_id == candidate_id)
    if email:
        query = query.filter(models.WebhookEvent.candidate_email == email)
    if job_id:
        query = query.filter(models.WebhookEvent.job_id == job_id)

    return (
        query.order_by(models.WebhookEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def list_webhook_events(db: Session, limit: int = 25, offset: int = 0) -> list[models.WebhookEvent]:
    """Return a paginated list of webhook events ordered by newest first."""
    return (
        db.query(models.WebhookEvent)
        .order_by(models.WebhookEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_events_by_candidate_id(db: Session, candidate_id: str) -> list[models.WebhookEvent]:
    """Return all webhook events for a given candidate identifier."""
    return (
        db.query(models.WebhookEvent)
        .filter(models.WebhookEvent.candidate_id == candidate_id)
        .order_by(models.WebhookEvent.created_at.desc())
        .all()
    )

import hashlib
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app import models


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def get_integration_by_company_and_provider(db: Session, company_id: str, provider: str) -> Optional[models.Integration]:
    return (
        db.query(models.Integration)
        .filter(models.Integration.company_id == company_id, models.Integration.provider == provider)
        .first()
    )


def get_api_key_for_company(db: Session, company_id: str) -> Optional[models.ApiKey]:
    return db.query(models.ApiKey).filter(models.ApiKey.company_id == company_id, models.ApiKey.status == "active").first()


def validate_api_key(db: Session, company_id: str, api_key: str) -> bool:
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
    return db.query(models.WebhookEvent).filter(models.WebhookEvent.event_id == event_id).first()

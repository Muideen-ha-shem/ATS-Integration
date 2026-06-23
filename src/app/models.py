import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Integration(Base):
    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(String(128), nullable=False, index=True)
    provider = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, default="active")
    callback_url = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(String(128), nullable=False, index=True)
    key_hash = Column(String(128), nullable=False, unique=True)
    status = Column(String(32), nullable=False, default="active")
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    event_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider = Column(String(64), nullable=False)
    company_id = Column(String(128), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(32), nullable=False, default="received")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    queued_at = Column(DateTime(timezone=True), nullable=True)

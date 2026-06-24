"""Pydantic schemas for validating inbound Workable webhook payloads."""

from typing import Any
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class CandidatePayload(BaseModel):
    """Candidate information provided inside the webhook payload."""
    id: str = Field(..., description="Workable candidate identifier")
    name: str = Field(..., description="Candidate full name")
    resume_url: HttpUrl = Field(..., description="Public or signed URL to candidate resume")


class WebhookData(BaseModel):
    """Wrapper for nested webhook event data."""
    candidate: CandidatePayload


class WorkableWebhookPayload(BaseModel):
    """Top-level model for Workable webhook events."""
    event: str = Field(..., description="Webhook event type, e.g. candidate_created")
    data: WebhookData


class WebhookEventResponse(BaseModel):
    """Response model used to return a saved webhook event."""
    event_id: str
    provider: str
    company_id: str
    event_type: str
    payload: dict[str, Any]
    status: str
    created_at: datetime
    queued_at: datetime | None = None

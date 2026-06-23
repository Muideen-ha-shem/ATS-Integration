"""Pydantic schemas for validating inbound Workable webhook payloads."""

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

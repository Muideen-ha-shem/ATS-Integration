from pydantic import BaseModel, Field, HttpUrl


class CandidatePayload(BaseModel):
    id: str = Field(..., description="Workable candidate identifier")
    name: str = Field(..., description="Candidate full name")
    resume_url: HttpUrl = Field(..., description="Public or signed URL to candidate resume")


class WebhookData(BaseModel):
    candidate: CandidatePayload


class WorkableWebhookPayload(BaseModel):
    event: str = Field(..., description="Webhook event type, e.g. candidate_created")
    data: WebhookData

"""Service utilities for processing ATS webhook events."""

from datetime import datetime
from typing import Any
from sqlalchemy.orm import object_session
from app import models


def _find_nested_value(source: Any, keys: list[str]) -> Any:
    if isinstance(source, dict):
        for key in keys:
            if key in source:
                return source[key]
        for value in source.values():
            found = _find_nested_value(value, keys)
            if found is not None:
                return found
    elif isinstance(source, list):
        for item in source:
            found = _find_nested_value(item, keys)
            if found is not None:
                return found
    return None


def extract_candidate_details(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract candidate and job metadata from a raw webhook payload."""
    try:
        candidate = _find_nested_value(payload, ["candidate"])
        job = _find_nested_value(payload, ["job"])

        candidate_id = None
        candidate_name = None
        candidate_email = None
        resume_url = None
        job_id = None
        job_title = None

        if isinstance(candidate, dict):
            candidate_id = candidate.get("id") or candidate.get("candidate_id")
            candidate_name = candidate.get("name") or candidate.get("full_name")
            candidate_email = candidate.get("email") or candidate.get("candidate_email")
            resume_url = candidate.get("resume_url") or candidate.get("resume")

        if isinstance(job, dict):
            job_id = job.get("id") or job.get("job_id")
            job_title = job.get("title") or job.get("job_title")

        if candidate_id is None:
            candidate_id = _find_nested_value(payload, ["candidate_id"])
        if candidate_name is None:
            candidate_name = _find_nested_value(payload, ["name", "full_name"])
        if candidate_email is None:
            candidate_email = _find_nested_value(payload, ["email", "candidate_email"])
        if resume_url is None:
            resume_url = _find_nested_value(payload, ["resume_url", "resume"])
        if job_id is None:
            job_id = _find_nested_value(payload, ["job_id"])
        if job_title is None:
            job_title = _find_nested_value(payload, ["title", "job_title"])

        return {
            "candidate_id": candidate_id,
            "candidate_name": candidate_name,
            "candidate_email": candidate_email,
            "resume_url": resume_url,
            "job_id": job_id,
            "job_title": job_title,
        }
    except Exception:
        return {
            "candidate_id": None,
            "candidate_name": None,
            "candidate_email": None,
            "resume_url": None,
            "job_id": None,
            "job_title": None,
        }


def queue_resume_for_scoring(event: models.WebhookEvent) -> None:
    """Mark the webhook event as queued and persist the update.

    In a production system, this service would typically publish a message to a
    queue or invoke an asynchronous worker responsible for resume scoring.
    """
    session = object_session(event)
    if session is None:
        raise RuntimeError("Webhook event is not bound to a session")

    event.status = "queued"
    event.queued_at = datetime.utcnow()
    session.add(event)
    session.commit()

    # TODO: integrate with your existing resume scoring pipeline.
    # At this point the ATS has delivered the resume event and the record is ready
    # for the scoring service to consume.

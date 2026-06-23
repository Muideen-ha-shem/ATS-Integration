from datetime import datetime

from sqlalchemy.orm import object_session

from app import models


def queue_resume_for_scoring(event: models.WebhookEvent) -> None:
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

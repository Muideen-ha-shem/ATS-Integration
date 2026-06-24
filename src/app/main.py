"""FastAPI application entrypoint for ATS Integration."""

import json
import logging
from typing import Any

from fastapi import Body, Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import crud, database, schemas, services

app = FastAPI(
    title="ATS Integration API",
    description="Receives ATS webhook events from Workable and queues resume scoring.",
    version="0.1.0",
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@app.on_event("startup")
def startup_event() -> None:
    """Initialize the database and seed sample data on application startup."""
    database.create_tables()
    database.upgrade_webhook_events_table_schema()
    database.seed_sample_data()

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Return a generic SQLAlchemy error response to the caller."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database error occurred."},
    )

@app.post("/api/webhooks/workable", status_code=status.HTTP_202_ACCEPTED)
async def workable_webhook(
    payload: dict[str, Any] = Body(...),
    x_api_key: str | None = Header(None, alias="X-Api-Key"),
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
    db: Session = Depends(database.get_db),
) -> dict[str, str]:
    """Process a Workable webhook request and queue the resume for scoring."""

    if not x_api_key or not x_company_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Api-Key and X-Company-Id headers are required.",
        )

    integration = crud.get_integration_by_company_and_provider(db, x_company_id, "workable")
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found for provided company and provider.",
        )

    if not crud.validate_api_key(db, x_company_id, x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )

    event = crud.create_webhook_event(
        db=db,
        provider="workable",
        company_id=x_company_id,
        event_type=payload.get("event", "unknown"),
        payload=payload,
        status="received",
    )

    metadata = services.extract_candidate_details(payload)
    try:
        crud.update_webhook_event_metadata(
            db=db,
            event_id=event.event_id,
            candidate_id=metadata.get("candidate_id"),
            candidate_name=metadata.get("candidate_name"),
            candidate_email=metadata.get("candidate_email"),
            resume_url=metadata.get("resume_url"),
            job_id=metadata.get("job_id"),
            job_title=metadata.get("job_title"),
        )
    except Exception:
        logger.exception("Failed to update webhook metadata for event_id=%s", event.event_id)

    logger.info(
        "Received webhook",
        extra={
            "event_id": event.event_id,
            "event_type": payload.get("event", "unknown"),
            "candidate_id": metadata.get("candidate_id"),
            "company_id": x_company_id,
        },
    )

    services.queue_resume_for_scoring(event)

    return {"status": "accepted", "event_id": event.event_id}


@app.get("/api/webhooks/workable/events/{event_id}", response_model=schemas.WebhookEventResponse)
async def get_workable_webhook_event(
    event_id: str,
    x_api_key: str | None = Header(None, alias="X-Api-Key"),
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
    db: Session = Depends(database.get_db),
):
    """Return a saved Workable webhook event so the candidate payload can be inspected."""
    if not x_api_key or not x_company_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Api-Key and X-Company-Id headers are required.",
        )

    integration = crud.get_integration_by_company_and_provider(db, x_company_id, "workable")
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found for provided company and provider.",
        )

    if not crud.validate_api_key(db, x_company_id, x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )

    event = crud.get_webhook_event_by_id(db, event_id)
    if not event or event.company_id != x_company_id or event.provider != "workable":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook event not found.",
        )

    return event


@app.get("/events/{event_id}", response_class=HTMLResponse)
async def render_webhook_event(
    event_id: str,
    x_api_key: str | None = Header(None, alias="X-Api-Key"),
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
    db: Session = Depends(database.get_db),
) -> HTMLResponse:
    """Render a simple HTML page showing the webhook event payload."""
    if not x_api_key or not x_company_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Api-Key and X-Company-Id headers are required.",
        )

    integration = crud.get_integration_by_company_and_provider(db, x_company_id, "workable")
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found for provided company and provider.",
        )

    if not crud.validate_api_key(db, x_company_id, x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )

    event = crud.get_webhook_event_by_id(db, event_id)
    if not event or event.company_id != x_company_id or event.provider != "workable":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook event not found.",
        )

    candidate = event.payload.get("data", {}).get("candidate", {})
    html_content = f"""
    <html>
        <head>
            <title>Webhook Event {event.event_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 2rem; }}
                .container {{ max-width: 800px; margin: auto; }}
                .card {{ border: 1px solid #ddd; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.05); }}
                h1 {{ font-size: 1.6rem; margin-bottom: 0.5rem; }}
                dt {{ font-weight: 700; margin-top: 0.75rem; }}
                dd {{ margin: 0 0 0.75rem 0; }}
                a {{ color: #0066cc; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <h1>Webhook Event {event.event_id}</h1>
                    <p><strong>Provider:</strong> {event.provider}</p>
                    <p><strong>Company ID:</strong> {event.company_id}</p>
                    <p><strong>Event Type:</strong> {event.event_type}</p>
                    <p><strong>Status:</strong> {event.status}</p>
                    <p><strong>Created At:</strong> {event.created_at}</p>
                    <p><strong>Queued At:</strong> {event.queued_at or 'Not queued yet'}</p>
                    <h2>Candidate Data</h2>
                    <dl>
                        <dt>Candidate ID</dt>
                        <dd>{candidate.get('id', 'N/A')}</dd>
                        <dt>Name</dt>
                        <dd>{candidate.get('name', 'N/A')}</dd>
                        <dt>Resume URL</dt>
                        <dd><a href="{candidate.get('resume_url', '#')}" target="_blank">{candidate.get('resume_url', 'N/A')}</a></dd>
                    </dl>
                </div>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=status.HTTP_200_OK)


@app.get("/api/candidates", response_model=list[schemas.CandidateSearchResponse])
async def search_candidates(
    candidate_id: str | None = None,
    email: str | None = None,
    job_id: str | None = None,
    limit: int = 25,
    offset: int = 0,
    x_api_key: str | None = Header(None, alias="X-Api-Key"),
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
    db: Session = Depends(database.get_db),
):
    if not x_api_key or not x_company_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Api-Key and X-Company-Id headers are required.",
        )

    integration = crud.get_integration_by_company_and_provider(db, x_company_id, "workable")
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found for provided company and provider.",
        )

    if not crud.validate_api_key(db, x_company_id, x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )

    events = crud.search_webhook_events(db, candidate_id=candidate_id, email=email, job_id=job_id, limit=limit, offset=offset)
    candidates: dict[str, dict[str, Any]] = {}
    for event in events:
        key = event.candidate_id or event.event_id
        summary = candidates.setdefault(key, {
            "candidate_id": event.candidate_id,
            "name": event.candidate_name,
            "email": event.candidate_email,
            "events": [],
        })
        summary["events"].append({
            "event_id": event.event_id,
            "event_type": event.event_type,
            "candidate_name": event.candidate_name,
            "candidate_email": event.candidate_email,
            "job_title": event.job_title,
            "created_at": event.created_at,
            "status": event.status,
        })

    return [schemas.CandidateSearchResponse(**candidate) for candidate in candidates.values()]


@app.get("/api/candidates/{candidate_id}", response_model=schemas.CandidateDetailResponse)
async def get_candidate_details(
    candidate_id: str,
    x_api_key: str | None = Header(None, alias="X-Api-Key"),
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
    db: Session = Depends(database.get_db),
):
    if not x_api_key or not x_company_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Api-Key and X-Company-Id headers are required.",
        )

    integration = crud.get_integration_by_company_and_provider(db, x_company_id, "workable")
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found for provided company and provider.",
        )

    if not crud.validate_api_key(db, x_company_id, x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )

    events = crud.get_events_by_candidate_id(db, candidate_id)
    if not events:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found.",
        )

    jobs = []
    for event in events:
        jobs.append({
            "job_id": event.job_id,
            "job_title": event.job_title,
        })

    return schemas.CandidateDetailResponse(
        candidate_id=candidate_id,
        name=events[0].candidate_name,
        email=events[0].candidate_email,
        resume_url=events[0].resume_url,
        jobs=[{"job_id": event.job_id, "job_title": event.job_title} for event in events if event.job_id or event.job_title],
        events=[{
            "event_id": event.event_id,
            "event_type": event.event_type,
            "candidate_name": event.candidate_name,
            "candidate_email": event.candidate_email,
            "job_title": event.job_title,
            "created_at": event.created_at,
            "status": event.status,
        } for event in events],
    )


@app.get("/events", response_class=HTMLResponse)
async def event_inbox_page(
    offset: int = 0,
    limit: int = 25,
    x_api_key: str | None = Header(None, alias="X-Api-Key"),
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
    db: Session = Depends(database.get_db),
) -> HTMLResponse:
    if not x_api_key or not x_company_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Api-Key and X-Company-Id headers are required.",
        )

    if not crud.get_integration_by_company_and_provider(db, x_company_id, "workable"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found for provided company and provider.",
        )

    if not crud.validate_api_key(db, x_company_id, x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )

    events = crud.list_webhook_events(db, limit=limit, offset=offset)
    rows = "".join([
        f"<tr>"
        f"<td><a href='/events/{event.event_id}?X-Api-Key={x_api_key}&X-Company-Id={x_company_id}'>{event.event_id}</a></td>"
        f"<td>{event.event_type}</td>"
        f"<td>{event.candidate_name or 'N/A'}</td>"
        f"<td>{event.candidate_email or 'N/A'}</td>"
        f"<td>{event.job_title or 'N/A'}</td>"
        f"<td>{event.created_at}</td>"
        f"<td>{event.status}</td>"
        f"</tr>"
        for event in events
    ])
    html = f"""
    <!doctype html>
    <html>
        <head>
            <meta charset='utf-8' />
            <title>Event Inbox</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 2rem; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
                th, td {{ border: 1px solid #ddd; padding: 0.75rem; text-align: left; }}
                th {{ background: #f6f8fa; }}
                a {{ color: #0066cc; text-decoration: none; }}
            </style>
        </head>
        <body>
            <h1>Event Inbox</h1>
            <p>Showing events {offset + 1} to {offset + len(events)}.</p>
            <table>
                <thead>
                    <tr>
                        <th>Event ID</th>
                        <th>Event Type</th>
                        <th>Candidate Name</th>
                        <th>Candidate Email</th>
                        <th>Job Title</th>
                        <th>Created At</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=status.HTTP_200_OK)


@app.get("/candidates", response_class=HTMLResponse)
async def candidate_explorer_page(
    candidate_id: str | None = None,
    email: str | None = None,
    x_api_key: str | None = Header(None, alias="X-Api-Key"),
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
    db: Session = Depends(database.get_db),
) -> HTMLResponse:
    if not x_api_key or not x_company_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Api-Key and X-Company-Id headers are required.",
        )

    if not crud.get_integration_by_company_and_provider(db, x_company_id, "workable"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found for provided company and provider.",
        )

    if not crud.validate_api_key(db, x_company_id, x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )

    search_events = crud.search_webhook_events(db, candidate_id=candidate_id, email=email, limit=25, offset=0)
    candidates: dict[str, dict[str, Any]] = {}
    for event in search_events:
        key = event.candidate_id or event.event_id
        if key not in candidates:
            candidates[key] = {
                "candidate_id": event.candidate_id,
                "name": event.candidate_name,
                "email": event.candidate_email,
                "latest_job_title": event.job_title,
                "latest_event_type": event.event_type,
                "latest_event_id": event.event_id,
            }

    rows = "".join([
        f"<tr>"
        f"<td><a href='/candidates/{candidate.get('candidate_id') or 'unknown'}?X-Api-Key={x_api_key}&X-Company-Id={x_company_id}'>{candidate.get('candidate_id') or 'N/A'}</a></td>"
        f"<td>{candidate.get('name') or 'N/A'}</td>"
        f"<td>{candidate.get('email') or 'N/A'}</td>"
        f"<td>{candidate.get('latest_job_title') or 'N/A'}</td>"
        f"<td>{candidate.get('latest_event_type') or 'N/A'}</td>"
        f"</tr>"
        for candidate in candidates.values()
    ])
    html = f"""
    <!doctype html>
    <html>
        <head>
            <meta charset='utf-8' />
            <title>Candidate Explorer</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 2rem; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
                th, td {{ border: 1px solid #ddd; padding: 0.75rem; text-align: left; }}
                th {{ background: #f6f8fa; }}
                a {{ color: #0066cc; text-decoration: none; }}
            </style>
        </head>
        <body>
            <h1>Candidate Explorer</h1>
            <form method='get'>
                <label>Candidate ID: <input name='candidate_id' value='{candidate_id or ''}' /></label>
                <label>Email: <input name='email' value='{email or ''}' /></label>
                <button type='submit'>Search</button>
            </form>
            <table>
                <thead>
                    <tr>
                        <th>Candidate ID</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Latest Job Applied</th>
                        <th>Latest Event</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=status.HTTP_200_OK)


@app.get("/candidates/{candidate_id}", response_class=HTMLResponse)
async def candidate_detail_page(
    candidate_id: str,
    x_api_key: str | None = Header(None, alias="X-Api-Key"),
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
    db: Session = Depends(database.get_db),
) -> HTMLResponse:
    if not x_api_key or not x_company_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Api-Key and X-Company-Id headers are required.",
        )

    if not crud.get_integration_by_company_and_provider(db, x_company_id, "workable"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found for provided company and provider.",
        )

    if not crud.validate_api_key(db, x_company_id, x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )

    events = crud.get_events_by_candidate_id(db, candidate_id)
    if not events:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found.",
        )

    resume_link = events[0].resume_url or '#'
    rows = "".join([
        f"<tr>"
        f"<td><a href='/events/{event.event_id}?X-Api-Key={x_api_key}&X-Company-Id={x_company_id}'>{event.event_id}</a></td>"
        f"<td>{event.event_type}</td>"
        f"<td>{event.job_title or 'N/A'}</td>"
        f"<td>{event.created_at}</td>"
        f"<td>{event.status}</td>"
        f"</tr>"
        for event in events
    ])
    html = f"""
    <!doctype html>
    <html>
        <head>
            <meta charset='utf-8' />
            <title>Candidate {candidate_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 2rem; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
                th, td {{ border: 1px solid #ddd; padding: 0.75rem; text-align: left; }}
                th {{ background: #f6f8fa; }}
                a {{ color: #0066cc; text-decoration: none; }}
                .button {{ display:inline-block; margin-top:1rem; padding:0.75rem 1rem; background:#0066cc; color:#fff; text-decoration:none; border-radius:6px; }}
            </style>
        </head>
        <body>
            <h1>Candidate Detail: {candidate_id}</h1>
            <p><strong>Name:</strong> {events[0].candidate_name or 'N/A'}</p>
            <p><strong>Email:</strong> {events[0].candidate_email or 'N/A'}</p>
            <p><strong>Resume URL:</strong> <a class='button' href='{resume_link}' target='_blank'>Open Resume</a></p>
            <h2>Applied Jobs</h2>
            <table>
                <thead>
                    <tr>
                        <th>Job ID</th>
                        <th>Job Title</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([f"<tr><td>{event.job_id or 'N/A'}</td><td>{event.job_title or 'N/A'}</td></tr>" for event in events if event.job_id or event.job_title])}
                </tbody>
            </table>
            <h2>Webhook Events</h2>
            <table>
                <thead>
                    <tr>
                        <th>Event ID</th>
                        <th>Event Type</th>
                        <th>Job Title</th>
                        <th>Created At</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            <h2>Raw Payload</h2>
            <pre>{json.dumps(events[0].payload, indent=2)}</pre>
        </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=status.HTTP_200_OK)


@app.get("/workable-test", response_class=HTMLResponse)
async def workable_test_page(
    x_api_key: str | None = Header(None, alias="X-Api-Key"),
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
    db: Session = Depends(database.get_db),
) -> HTMLResponse:
    if not x_api_key or not x_company_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Api-Key and X-Company-Id headers are required.",
        )

    if not crud.get_integration_by_company_and_provider(db, x_company_id, "workable"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found for provided company and provider.",
        )

    if not crud.validate_api_key(db, x_company_id, x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )

    events = crud.list_webhook_events(db, limit=20, offset=0)
    rows = "".join([
        f"<tr>"
        f"<td>{event.event_id}</td>"
        f"<td>{event.event_type}</td>"
        f"<td>{event.candidate_name or 'N/A'}</td>"
        f"<td>{event.candidate_email or 'N/A'}</td>"
        f"<td><a href='{event.resume_url or '#'}' target='_blank'>{event.resume_url or 'N/A'}</a></td>"
        f"<td>{event.job_title or 'N/A'}</td>"
        f"<td>{event.created_at}</td>"
        f"</tr>"
        for event in events
    ])
    html = f"""
    <!doctype html>
    <html>
        <head>
            <meta charset='utf-8' />
            <title>Workable Testing Mode</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 2rem; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
                th, td {{ border: 1px solid #ddd; padding: 0.75rem; text-align: left; }}
                th {{ background: #f6f8fa; }}
                a {{ color: #0066cc; text-decoration: none; }}
            </style>
        </head>
        <body>
            <h1>Workable Testing Mode</h1>
            <table>
                <thead>
                    <tr>
                        <th>Event ID</th>
                        <th>Event Type</th>
                        <th>Candidate Name</th>
                        <th>Candidate Email</th>
                        <th>Resume URL</th>
                        <th>Job Title</th>
                        <th>Received Timestamp</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=status.HTTP_200_OK)


@app.get("/ui", response_class=HTMLResponse)
async def ui_page() -> HTMLResponse:
        """Simple browser UI to lookup and display webhook events.

        The page lets you enter an `event_id` and the required headers, then
        fetches the JSON event from the API and renders it on the page.
        """
        html = """
        <!doctype html>
        <html>
            <head>
                <meta charset="utf-8" />
                <title>Webhook Event Viewer</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 2rem; }
                    .container { max-width: 800px; margin: auto; }
                    label { display:block; margin-top: 0.75rem; font-weight:600 }
                    input[type=text] { width:100%; padding:0.5rem; box-sizing:border-box }
                    button { margin-top: 1rem; padding:0.5rem 1rem }
                    pre { background:#f6f8fa; padding:1rem; border-radius:6px; overflow:auto }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Webhook Event Viewer</h1>
                    <form id="lookup">
                        <label>Event ID
                            <input id="event_id" type="text" placeholder="706076d4-..." />
                        </label>
                        <label>X-Api-Key
                            <input id="x_api_key" type="text" placeholder="sk_test_company_123" />
                        </label>
                        <label>X-Company-Id
                            <input id="x_company_id" type="text" placeholder="company_123" />
                        </label>
                        <button type="submit">Load Event</button>
                    </form>

                    <h2>Result</h2>
                    <div id="result">No event loaded.</div>
                </div>

                <script>
                    const form = document.getElementById('lookup');
                    const result = document.getElementById('result');
                    form.addEventListener('submit', async (e) => {
                        e.preventDefault();
                        const eventId = document.getElementById('event_id').value.trim();
                        const apiKey = document.getElementById('x_api_key').value.trim();
                        const companyId = document.getElementById('x_company_id').value.trim();
                        if (!eventId) { result.innerText = 'Please enter an event_id'; return }
                        try {
                            result.innerText = 'Loading...';
                            const resp = await fetch(`/api/webhooks/workable/events/${eventId}`, {
                                headers: {
                                    'X-Api-Key': apiKey,
                                    'X-Company-Id': companyId,
                                }
                            });
                            if (!resp.ok) {
                                const text = await resp.text();
                                result.innerHTML = `<pre>${resp.status} ${resp.statusText}\n${text}</pre>`;
                                return;
                            }
                            const data = await resp.json();
                            // Render a small HTML summary and raw JSON
                            const candidate = (data.payload && data.payload.data && data.payload.data.candidate) || {};
                            result.innerHTML = `
                                <div class="card">
                                    <p><strong>Provider:</strong> ${data.provider}</p>
                                    <p><strong>Company ID:</strong> ${data.company_id}</p>
                                    <p><strong>Event Type:</strong> ${data.event_type}</p>
                                    <p><strong>Status:</strong> ${data.status}</p>
                                    <h3>Candidate</h3>
                                    <p><strong>ID:</strong> ${candidate.id || candidate['id'] || 'N/A'}</p>
                                    <p><strong>Name:</strong> ${candidate.name || candidate['name'] || 'N/A'}</p>
                                    <p><strong>Resume:</strong> <a href="${candidate.resume_url || candidate['resume_url'] || '#'}" target="_blank">${candidate.resume_url || candidate['resume_url'] || 'N/A'}</a></p>
                                </div>
                                <h4>Raw JSON</h4>
                                <pre>${JSON.stringify(data, null, 2)}</pre>
                            `;
                        } catch (err) {
                            result.innerHTML = `<pre>${err}</pre>`;
                        }
                    });
                </script>
            </body>
        </html>
        """
        return HTMLResponse(content=html, status_code=status.HTTP_200_OK)


@app.get("/")
async def root() -> dict[str, str]:
        """Return the root page."""
        return {"message": "ATS Integration API is running"}
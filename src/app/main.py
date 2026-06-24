"""FastAPI application entrypoint for ATS Integration."""

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import crud, database, schemas, services

app = FastAPI(
    title="ATS Integration API",
    description="Receives ATS webhook events from Workable and queues resume scoring.",
    version="0.1.0",
)

@app.on_event("startup")
def startup_event() -> None:
    """Initialize the database and seed sample data on application startup."""
    database.create_tables()
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
    payload: schemas.WorkableWebhookPayload,
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
        event_type=payload.event,
        payload=payload.model_dump(mode="json"),
        status="received",
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
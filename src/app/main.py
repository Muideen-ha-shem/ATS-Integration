"""FastAPI application entrypoint for ATS Integration."""

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
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


@app.get("/")
async def root() -> dict[str, str]:
    """Return the root page."""
    return {"message": "ATS Integration API is running"}
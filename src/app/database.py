"""Database configuration and helper utilities for ATS Integration."""

import os
from datetime import datetime
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ats_integration.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Base declarative class for SQLAlchemy models."""
    pass


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for dependency injection."""
    with SessionLocal() as session:
        yield session


def create_tables() -> None:
    """Create all database tables using SQLAlchemy metadata."""
    Base.metadata.create_all(bind=engine)


def upgrade_webhook_events_table_schema() -> None:
    """Add new extracted metadata columns to the webhook_events table if missing."""
    with engine.begin() as conn:
        result = conn.execute(text("PRAGMA table_info('webhook_events')"))
        existing_columns = {row[1] for row in result.fetchall()}
        columns_to_add = [
            ("candidate_id", "TEXT"),
            ("candidate_name", "TEXT"),
            ("candidate_email", "TEXT"),
            ("resume_url", "TEXT"),
            ("job_id", "TEXT"),
            ("job_title", "TEXT"),
        ]
        for column_name, column_type in columns_to_add:
            if column_name not in existing_columns:
                conn.execute(text(f"ALTER TABLE webhook_events ADD COLUMN {column_name} {column_type}"))


def seed_sample_data() -> None:
    """Seed example integration and API key records for local development."""
    from app import crud

    with SessionLocal() as session:
        if not crud.get_integration_by_company_and_provider(session, "company_123", "workable"):
            crud.create_integration(
                db=session,
                company_id="company_123",
                provider="workable",
                status="active",
                callback_url="https://yourplatform.com/api/callbacks/workable",
            )
        if not crud.get_api_key_for_company(session, "company_123"):
            crud.create_api_key(
                db=session,
                company_id="company_123",
                plain_key="sk_test_company_123",
                status="active",
            )

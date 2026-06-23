import os
from datetime import datetime

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app import models, crud

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ats_integration.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Session:
    with SessionLocal() as session:
        yield session


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


def seed_sample_data() -> None:
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

import json
import logging
from pathlib import Path
from typing import Generator
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session

from src.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

Base = declarative_base()


class OpportunityTable(Base):
    __tablename__ = "opportunities"

    id = Column(String(128), primary_key=True)
    title = Column(String(512), nullable=False)
    problem_statement = Column(Text, nullable=False)

    organization_name = Column(String(256), nullable=False)
    organization_type = Column(String(64), nullable=False)
    organization_level = Column(String(64), nullable=True)

    opportunity_type = Column(String(64), nullable=False)
    source_opportunity_type = Column(String(128), nullable=True)

    domains = Column(Text, default="[]")  # JSON encoded list of strings
    country = Column(String(128), default="India")
    region = Column(String(128), nullable=True)
    city = Column(String(128), nullable=True)

    status = Column(String(32), default="ACTIVE")  # ACTIVE, CLOSED, EXPIRED

    published_date = Column(String(64), nullable=True)
    deadline = Column(String(64), nullable=True)

    prize_amount = Column(Float, nullable=True)
    prize_currency = Column(String(16), default="INR")
    prize_raw = Column(String(128), nullable=True)

    funding_amount = Column(Float, nullable=True)
    funding_currency = Column(String(16), default="INR")
    funding_raw = Column(String(128), nullable=True)

    support_description = Column(Text, nullable=True)

    eligibility = Column(Text, default="[]")     # JSON encoded list
    requirements = Column(Text, default="[]")    # JSON encoded list
    constraints = Column(Text, default="[]")     # JSON encoded list
    expected_outcome = Column(Text, nullable=True)

    verification_status = Column(String(32), default="VERIFIED_OFFICIAL")
    source_url = Column(String(1024), nullable=False)
    source_domain = Column(String(256), nullable=False)
    source_title = Column(String(512), nullable=True)

    source_evidence = Column(Text, default="[]")  # JSON encoded list of evidence dicts

    version = Column(Integer, default=1)
    unverified_duplicate_of = Column(String(128), nullable=True)

    first_seen_at = Column(DateTime, nullable=False)
    last_verified_at = Column(DateTime, nullable=False)
    last_changed_at = Column(DateTime, nullable=True)

    # Relationships
    versions = relationship("VersionTable", back_populates="opportunity", cascade="all, delete-orphan")


class SourceTable(Base):
    __tablename__ = "sources"

    source_id = Column(String(128), primary_key=True)
    name = Column(String(256), nullable=False)
    organization = Column(String(256), nullable=False)
    organization_type = Column(String(64), default="government")
    country = Column(String(16), default="IN")
    authority_level = Column(String(32), default="official")
    base_url = Column(String(1024), nullable=False)
    enabled = Column(Boolean, default=True)
    adapter = Column(String(128), nullable=False)
    discovery_frequency = Column(String(32), default="daily")
    last_run_at = Column(DateTime, nullable=True)


class VersionTable(Base):
    __tablename__ = "opportunity_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    opportunity_id = Column(String(128), ForeignKey("opportunities.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    changed_at = Column(DateTime, nullable=False)
    change_reason = Column(String(128), default="source_update")
    diffs = Column(Text, default="[]")       # JSON encoded field diffs
    snapshot = Column(Text, default="{}")    # JSON encoded full opportunity snapshot

    opportunity = relationship("OpportunityTable", back_populates="versions")


def get_engine():
    """Create SQLAlchemy engine with automatic SQLite fallback."""
    if settings.USE_SQLITE_FALLBACK:
        db_path = Path(settings.SQLITE_DB_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        sqlite_url = f"sqlite:///{db_path.resolve()}"
        return create_engine(sqlite_url, connect_args={"check_same_thread": False})
    
    try:
        engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
        # Test connection
        with engine.connect() as conn:
            pass
        return engine
    except Exception as e:
        logger.warning(f"Could not connect to PostgreSQL ({e}). Falling back to local SQLite.")
        db_path = Path(settings.SQLITE_DB_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return create_engine(f"sqlite:///{db_path.resolve()}", connect_args={"check_same_thread": False})


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

import os
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    ForeignKey,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DB_PATH = Path(__file__).resolve().parent / "docuverify.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class VerifiedRegistry(Base):
    __tablename__ = "verified_registry"

    id = Column(Integer, primary_key=True, index=True)
    student_name = Column(String(128), nullable=False, index=True)
    student_id_raw = Column(String(64), nullable=False)
    student_id_hash = Column(String(64), unique=True, nullable=False, index=True)
    course = Column(String(128), nullable=False)
    institution = Column(String(256), nullable=False)
    marks_or_grade = Column(String(64), nullable=False)
    issue_year = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    audit_logs = relationship("VerificationAuditLog", back_populates="matched_record")


class VerificationAuditLog(Base):
    __tablename__ = "verification_audit_log"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(256), nullable=False)
    document_hash = Column(String(64), nullable=False, index=True)
    detected_name = Column(String(128), nullable=True)
    detected_id = Column(String(64), nullable=True)
    matched_record_id = Column(Integer, ForeignKey("verified_registry.id"), nullable=True)
    match_status = Column(String(32), nullable=False)  # VERIFIED, TAMPERED_SUSPECT, MISMATCH, NOT_FOUND
    tamper_risk_score = Column(Float, nullable=False)
    tamper_level = Column(String(16), nullable=False)  # LOW, MODERATE, HIGH, CRITICAL
    details_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    matched_record = relationship("VerifiedRegistry", back_populates="audit_logs")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

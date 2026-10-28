"""
Veritabanı katmanı (4. hafta, Hedef 4.3)

SQLAlchemy ORM; tablo tanımları backend/db/schema.sql ile birebir aynıdır.
Bağlantı DATABASE_URL ortam değişkeninden okunur:
  PostgreSQL : postgresql+psycopg://kredilens:kredilens@localhost:5432/kredilens  (docker compose up -d db)
  Geliştirme : sqlite:///backend/db/dev.sqlite3  (varsayılan; sunucu kurulumu gerekmez)
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Iterator

from sqlalchemy import JSON, BigInteger, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, SmallInteger, Text, create_engine, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_URL = f"sqlite:///{ROOT / 'backend' / 'db' / 'dev.sqlite3'}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_URL)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

PK = BigInteger().with_variant(Integer, "sqlite")        # SQLite'ta otomatik artış için INTEGER gerekir
JSONType = JSON().with_variant(JSONB, "postgresql")


class Base(DeclarativeBase):
    pass


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(PK, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    loan_amnt: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    annual_inc: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    dti: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    emp_length: Mapped[str | None] = mapped_column(Text)
    home_ownership: Mapped[str] = mapped_column(Text, nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    fico_range_low: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    fico_range_high: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    open_acc: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    delinq_2yrs: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    revol_util: Mapped[float | None] = mapped_column(Numeric(6, 2))
    inq_last_6mths: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    earliest_cr_line: Mapped[str] = mapped_column(Text, nullable=False)

    predictions: Mapped[list["Prediction"]] = relationship(back_populates="application", cascade="all, delete-orphan",
                                                           order_by="Prediction.scored_at.desc()")


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (CheckConstraint("risk_group IN ('Düşük', 'Orta', 'Yüksek')", name="ck_predictions_risk_group"),)

    id: Mapped[int] = mapped_column(PK, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    model_version: Mapped[str] = mapped_column(Text, nullable=False)
    default_probability: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    risk_group: Mapped[str] = mapped_column(Text, nullable=False)
    reasons: Mapped[list] = mapped_column(JSONType, nullable=False, default=list)

    application: Mapped[Application] = relationship(back_populates="predictions")


def init_db() -> None:
    Base.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


def dialect_name() -> str:
    return engine.dialect.name

"""SQLAlchemy models for the CampusFix maintenance ticketing system."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Ticket(Base):
    """A single campus maintenance / IT support ticket.

    One row represents one reported issue plus its lifecycle in the
    OPEN -> IN_PROGRESS -> RESOLVED workflow.
    """

    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[str] = mapped_column(String(30), nullable=False, default="IT_SUPPORT")
    building: Mapped[str] = mapped_column(String(120), nullable=False, default="Unspecified")
    reporter: Mapped[str] = mapped_column(String(120), nullable=False, default="Unknown")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="OPEN")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<Ticket id={self.id} status={self.status} title={self.title!r}>"
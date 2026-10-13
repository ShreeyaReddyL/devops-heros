"""Pydantic request/response schemas and workflow rules for CampusFix."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

TicketStatus = Literal["OPEN", "IN_PROGRESS", "RESOLVED"]
TicketPriority = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
TicketCategory = Literal[
    "WI_FI",
    "PROJECTOR",
    "ELECTRICAL",
    "PLUMBING",
    "HOSTEL",
    "LAB_EQUIPMENT",
    "IT_SUPPORT",
    "OTHER",
]

#: Documented ticket workflow. A ticket may stay in its current state, move
#: forward, or be reopened. RESOLVED tickets can only be reopened or closed.
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "OPEN": frozenset({"OPEN", "IN_PROGRESS", "RESOLVED"}),
    "IN_PROGRESS": frozenset({"IN_PROGRESS", "RESOLVED", "OPEN"}),
    "RESOLVED": frozenset({"RESOLVED", "OPEN"}),
}


class TicketCreate(BaseModel):
    """Payload accepted by POST /api/tickets."""

    title: str = Field(min_length=5, max_length=200)
    description: str = Field(default="", max_length=4000)
    category: TicketCategory = "IT_SUPPORT"
    building: str = Field(default="Unspecified", min_length=2, max_length=120)
    reporter: str = Field(default="Unknown", min_length=2, max_length=120)
    priority: TicketPriority = "MEDIUM"
    status: TicketStatus = "OPEN"

    @field_validator("title", "building", "reporter")
    @classmethod
    def _require_non_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned

    @field_validator("description")
    @classmethod
    def _strip_description(cls, value: str) -> str:
        return value.strip()


class TicketUpdate(BaseModel):
    """Payload accepted by PUT /api/tickets/{ticket_id}.

    Every field is optional, but at least one field must be supplied so that an
    empty PUT is rejected instead of silently succeeding.
    """

    title: str | None = Field(default=None, min_length=5, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    category: TicketCategory | None = None
    building: str | None = Field(default=None, min_length=2, max_length=120)
    reporter: str | None = Field(default=None, min_length=2, max_length=120)
    priority: TicketPriority | None = None
    status: TicketStatus | None = None

    @field_validator("title", "building", "reporter")
    @classmethod
    def _require_non_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned

    @field_validator("description")
    @classmethod
    def _strip_description(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def _at_least_one_field(self) -> "TicketUpdate":
        if not self.model_dump(exclude_unset=True):
            raise ValueError("at least one field must be supplied")
        return self


class TicketOut(BaseModel):
    """Ticket representation returned by every ticket endpoint."""

    id: int
    title: str
    description: str
    category: TicketCategory
    building: str
    reporter: str
    priority: TicketPriority
    status: TicketStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoryCount(BaseModel):
    category: str
    count: int


class StatsOut(BaseModel):
    """Aggregated ticket statistics computed from live database rows."""

    total: int
    open: int
    in_progress: int
    resolved: int
    critical: int
    high: int
    by_category: list[CategoryCount]
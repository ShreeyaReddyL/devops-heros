"""CampusFix API - campus maintenance and IT support ticketing service."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import settings
from .db import Base, engine, get_db
from .models import Ticket
from .schemas import (
    ALLOWED_TRANSITIONS,
    CategoryCount,
    StatsOut,
    TicketCreate,
    TicketOut,
    TicketUpdate,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create the schema on startup.

    Container images run ``alembic upgrade head`` before Uvicorn starts, so this
    is a no-op in production and only matters for local runs against SQLite.
    """
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=(
        "CampusFix - report and track campus maintenance and IT support issues "
        "across Wi-Fi, projectors, electrical, plumbing, hostel and lab equipment."
    ),
    lifespan=lifespan,
)

# The frontend is served by Nginx, but this keeps `npm run dev` usable too.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# /metrics is scraped by Prometheus via the Helm ServiceMonitor.
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {"service": settings.app_name, "version": settings.version, "docs": "/docs"}


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Liveness probe. Never touches the database so it cannot hang."""
    return {"status": "UP", "service": settings.app_name, "version": settings.version}


@app.get("/ready", tags=["meta"])
def ready(db: Session = Depends(get_db)) -> dict[str, str]:
    """Readiness probe. Executes a real query so it fails if the DB is down."""
    db.execute(select(func.count(Ticket.id)))
    return {"status": "READY"}


# --------------------------------------------------------------------------- #
# Ticket endpoints
# --------------------------------------------------------------------------- #


@app.get("/api/tickets", response_model=list[TicketOut], tags=["tickets"])
def list_tickets(
    db: Session = Depends(get_db),
    status_filter: str | None = Query(default=None, alias="status", max_length=30),
    category: str | None = Query(default=None, max_length=30),
    priority: str | None = Query(default=None, max_length=20),
) -> list[Ticket]:
    """List tickets, newest first, with optional status/category/priority filters."""
    stmt = select(Ticket)
    if status_filter:
        stmt = stmt.where(Ticket.status == status_filter.strip().upper())
    if category:
        stmt = stmt.where(Ticket.category == category.strip().upper())
    if priority:
        stmt = stmt.where(Ticket.priority == priority.strip().upper())
    return list(db.scalars(stmt.order_by(Ticket.id.desc())))


@app.get("/api/tickets/stats", response_model=StatsOut, tags=["tickets"])
def ticket_stats(db: Session = Depends(get_db)) -> StatsOut:
    """Aggregate ticket counts by status, priority and category."""
    status_rows = db.execute(
        select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)
    ).all()
    status_counts = {value: count for value, count in status_rows}

    priority_rows = db.execute(
        select(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority)
    ).all()
    priority_counts = {value: count for value, count in priority_rows}

    category_rows = db.execute(
        select(Ticket.category, func.count(Ticket.id))
        .group_by(Ticket.category)
        .order_by(func.count(Ticket.id).desc())
    ).all()

    return StatsOut(
        total=sum(status_counts.values()),
        open=status_counts.get("OPEN", 0),
        in_progress=status_counts.get("IN_PROGRESS", 0),
        resolved=status_counts.get("RESOLVED", 0),
        critical=priority_counts.get("CRITICAL", 0),
        high=priority_counts.get("HIGH", 0),
        by_category=[CategoryCount(category=name, count=count) for name, count in category_rows],
    )


@app.get("/api/tickets/{ticket_id}", response_model=TicketOut, tags=["tickets"])
def get_ticket(ticket_id: int, db: Session = Depends(get_db)) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return ticket


@app.post(
    "/api/tickets",
    response_model=TicketOut,
    status_code=status.HTTP_201_CREATED,
    tags=["tickets"],
)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)) -> Ticket:
    ticket = Ticket(**payload.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@app.put("/api/tickets/{ticket_id}", response_model=TicketOut, tags=["tickets"])
def update_ticket(ticket_id: int, payload: TicketUpdate, db: Session = Depends(get_db)) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    changes = payload.model_dump(exclude_unset=True)
    new_status = changes.get("status")
    if new_status is not None and new_status not in ALLOWED_TRANSITIONS[ticket.status]:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Illegal status transition {ticket.status} -> {new_status}. "
                f"Allowed: {sorted(ALLOWED_TRANSITIONS[ticket.status])}"
            ),
        )

    for field, value in changes.items():
        setattr(ticket, field, value)
    db.commit()
    db.refresh(ticket)
    return ticket


@app.delete(
    "/api/tickets/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["tickets"],
)
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)) -> Response:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    db.delete(ticket)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
"""Forward migration: TaskBoard `tasks` table -> CampusFix `tickets` table.

The Session 21 starter shipped migration 0001 which created a `tasks` table.
That revision may already be applied in an existing environment, so this
migration moves forward from it instead of rewriting the applied history.
Existing rows are preserved: they are re-labelled into the CampusFix workflow
and mapped onto the new category/building/reporter columns.
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_campusfix_tickets"
down_revision = "0001_create_tasks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("tasks", "tickets")

    op.add_column(
        "tickets",
        sa.Column("category", sa.String(length=30), nullable=False, server_default="IT_SUPPORT"),
    )
    op.add_column(
        "tickets",
        sa.Column("building", sa.String(length=120), nullable=False, server_default="Unspecified"),
    )
    op.add_column(
        "tickets",
        sa.Column("reporter", sa.String(length=120), nullable=False, server_default="Unknown"),
    )

    # Map the old TaskBoard vocabulary onto the CampusFix workflow, carrying the
    # old assignee across as the reporter so no reported work is lost.
    op.execute("UPDATE tickets SET status = 'OPEN' WHERE status = 'TODO'")
    op.execute("UPDATE tickets SET status = 'RESOLVED' WHERE status = 'DONE'")
    op.execute("UPDATE tickets SET reporter = assignee WHERE assignee <> 'Unassigned'")
    op.execute("UPDATE tickets SET building = 'Imported from TaskBoard'")

    # The old server_default was 'TODO', which is not a valid TicketStatus.
    # batch_alter_table is required so this also works on SQLite.
    with op.batch_alter_table("tickets") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=30),
            existing_nullable=False,
            server_default="OPEN",
        )

    op.drop_column("tickets", "assignee")


def downgrade() -> None:
    op.add_column(
        "tickets",
        sa.Column("assignee", sa.String(length=120), nullable=False, server_default="Unassigned"),
    )
    op.execute("UPDATE tickets SET assignee = reporter")

    op.drop_column("tickets", "building")
    op.drop_column("tickets", "category")
    op.drop_column("tickets", "reporter")
    op.rename_table("tickets", "tasks")
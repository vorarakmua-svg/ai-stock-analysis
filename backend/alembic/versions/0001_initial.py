"""initial persistence schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-20
"""

import sqlalchemy as sa

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "valuations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("owner_id", sa.String(length=64), nullable=True, index=True),
        sa.Column("ticker", sa.String(length=16), nullable=False, index=True),
        sa.Column("composite_intrinsic_value", sa.Float(), nullable=True),
        sa.Column("verdict", sa.String(length=64), nullable=True),
        sa.Column("extraction_timestamp", sa.String(length=64), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "extractions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("owner_id", sa.String(length=64), nullable=True, index=True),
        sa.Column("ticker", sa.String(length=16), nullable=False, index=True),
        sa.Column("collected_at", sa.String(length=64), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "llm_usage",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("owner_id", sa.String(length=64), nullable=True, index=True),
        sa.Column("purpose", sa.String(length=64), nullable=False, index=True),
        sa.Column("ticker", sa.String(length=16), nullable=True, index=True),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("thinking_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_at", sa.String(length=64), nullable=False),
        sa.Column("total", sa.Integer(), nullable=True),
        sa.Column("written", sa.Integer(), nullable=True),
        sa.Column("unchanged", sa.Integer(), nullable=True),
        sa.Column("errors", sa.Integer(), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("ingestion_runs")
    op.drop_table("llm_usage")
    op.drop_table("extractions")
    op.drop_table("valuations")

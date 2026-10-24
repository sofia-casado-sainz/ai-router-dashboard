"""Catálogo persistente de modelos: tablas models y model_prices.

Solo esquema: los datos de ejemplo se cargan con scripts/seed_models.py.

Revision ID: 0001
Revises:
Create Date: 2026-10-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "models",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_key", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("context_window", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_models")),
        sa.UniqueConstraint("provider", "model_key", name=op.f("uq_models_provider_model_key")),
        sa.CheckConstraint("context_window > 0", name=op.f("ck_models_context_window_positive")),
    )

    op.create_table(
        "model_prices",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("model_id", sa.Uuid(), nullable=False),
        sa.Column("input_cost_per_million", sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column("output_cost_per_million", sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_model_prices")),
        sa.ForeignKeyConstraint(
            ["model_id"],
            ["models.id"],
            name=op.f("fk_model_prices_model_id_models"),
            ondelete="CASCADE",
        ),
        # Índice para el precio vigente de un modelo; también cubre la clave foránea.
        sa.UniqueConstraint("model_id", "valid_from", name=op.f("uq_model_prices_model_id_valid_from")),
        sa.CheckConstraint(
            "input_cost_per_million >= 0", name=op.f("ck_model_prices_input_cost_non_negative")
        ),
        sa.CheckConstraint(
            "output_cost_per_million >= 0", name=op.f("ck_model_prices_output_cost_non_negative")
        ),
        sa.CheckConstraint(
            "length(currency) = 3 AND currency = upper(currency)",
            name=op.f("ck_model_prices_currency_iso_4217"),
        ),
    )


def downgrade() -> None:
    op.drop_table("model_prices")
    op.drop_table("models")

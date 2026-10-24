"""Catálogo: dónde se ejecuta cada modelo (ADR-0001).

Añade `inference_provider` (sistema que ejecuta el modelo: openrouter, ollama,
fake…) y `provider_model_id` (identificador del modelo en ese sistema). Son
opcionales: un modelo sin ellos todavía no se puede ejecutar. Solo esquema; el
seed rellena los valores de los modelos de ejemplo.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("models", sa.Column("inference_provider", sa.String(length=64), nullable=True))
    op.add_column("models", sa.Column("provider_model_id", sa.String(length=255), nullable=True))
    # Ambos campos o ninguno: un modelo no puede ser ejecutable a medias.
    op.create_check_constraint(
        op.f("ck_models_execution_target_complete"),
        "models",
        "(inference_provider IS NULL) = (provider_model_id IS NULL)",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_models_execution_target_complete"), "models", type_="check")
    op.drop_column("models", "provider_model_id")
    op.drop_column("models", "inference_provider")

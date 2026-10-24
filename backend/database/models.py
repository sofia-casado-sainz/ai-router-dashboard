"""Tablas del catálogo de modelos (ORM). Solo las usan los repositorios, el seed y Alembic."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# Precio en unidades de moneda por millón de tokens, con 6 decimales.
PRICE_TYPE = Numeric(12, 6)


class ModelRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "models"
    __table_args__ = (
        # La misma clave puede existir en proveedores distintos (p. ej. un modelo
        # abierto servido por OpenRouter y por Ollama).
        UniqueConstraint("provider", "model_key"),
        CheckConstraint("context_window > 0", name="context_window_positive"),
        # Un modelo es ejecutable con ambos campos o con ninguno, nunca a medias.
        CheckConstraint(
            "(inference_provider IS NULL) = (provider_model_id IS NULL)",
            name="execution_target_complete",
        ),
    )

    # Proveedor del modelo como slug en minúsculas: openai, anthropic, ollama…
    provider: Mapped[str] = mapped_column(String(64))
    # Identificador del modelo en ese proveedor.
    model_key: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(255))
    # Tamaño máximo de contexto, en tokens.
    context_window: Mapped[int] = mapped_column(Integer)
    # Si el router puede usarlo.
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    # Sistema que ejecuta el modelo (openrouter, ollama, fake…), distinto del vendor
    # (`provider`). NULL: el modelo todavía no se puede ejecutar (ADR-0001).
    inference_provider: Mapped[str | None] = mapped_column(String(64), default=None)
    # Identificador del modelo en ese sistema de ejecución.
    provider_model_id: Mapped[str | None] = mapped_column(String(255), default=None)

    prices: Mapped[list[ModelPriceRecord]] = relationship(
        back_populates="model", cascade="all, delete-orphan", passive_deletes=True
    )


class ModelPriceRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Histórico de precios: el vigente es el de `valid_from` más reciente que no sea futuro."""

    __tablename__ = "model_prices"
    __table_args__ = (
        # También sirve de índice para buscar el precio vigente de un modelo.
        UniqueConstraint("model_id", "valid_from"),
        CheckConstraint("input_cost_per_million >= 0", name="input_cost_non_negative"),
        CheckConstraint("output_cost_per_million >= 0", name="output_cost_non_negative"),
        CheckConstraint(
            "length(currency) = 3 AND currency = upper(currency)", name="currency_iso_4217"
        ),
    )

    model_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("models.id", ondelete="CASCADE"))
    input_cost_per_million: Mapped[Decimal] = mapped_column(PRICE_TYPE)
    output_cost_per_million: Mapped[Decimal] = mapped_column(PRICE_TYPE)
    # Código ISO 4217 (USD, EUR…).
    currency: Mapped[str] = mapped_column(String(3))
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    model: Mapped[ModelRecord] = relationship(back_populates="prices")

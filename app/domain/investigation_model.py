from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import (
    JSONB,
    UUID as PostgreSQLUUID,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.core.database import Base


class IncidentInvestigation(Base):
    __tablename__ = "incident_investigations"

    investigation_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    incident_id: Mapped[str] = mapped_column(
        ForeignKey(
            "incidents.incident_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    service_now_number: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    investigation_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="STARTED",
    )

    analysis_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    probable_root_cause: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    suspected_component: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    release_related: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    release_confidence: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=0,
    )

    regression_related: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    regression_confidence: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=0,
    )

    recommended_mitigation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    recommended_code_fix: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    recommended_tests: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    analysis_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    requires_human_approval: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    approval_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    evidence_items = relationship(
        "InvestigationEvidence",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )
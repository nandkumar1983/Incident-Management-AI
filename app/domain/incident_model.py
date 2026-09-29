from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.core.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    incident_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    application_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    environment: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="OPEN",
    )

    source_system: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="MANUAL",
    )

    source_event_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    datadog_monitor_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    datadog_alert_status: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    service_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    host_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    deployed_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    service_now_sys_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    service_now_number: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    assignment_group: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    integration_status: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    integration_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
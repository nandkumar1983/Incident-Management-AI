from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class IncidentRequest(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=5)
    application_name: str = Field(min_length=2, max_length=100)
    environment: str = Field(min_length=2, max_length=50)


class IncidentResponse(BaseModel):
    incident_id: str
    title: str
    description: str
    application_name: str
    environment: str
    severity: str
    status: str
    source_system: str
    service_now_number: str | None = None
    created_at: datetime | None = None


class IncidentStatusUpdate(BaseModel):
    status: Literal[
        "OPEN",
        "ASSIGNED",
        "IN_PROGRESS",
        "RESOLVED",
        "CLOSED",
    ]


class DatadogAlertRequest(BaseModel):
    event_id: str = Field(min_length=1)
    monitor_id: str | None = None
    monitor_name: str = Field(min_length=1)
    alert_status: str = Field(min_length=1)
    alert_title: str = Field(min_length=1)
    alert_message: str = Field(min_length=1)
    application_name: str = Field(min_length=1)
    environment: str = Field(min_length=1)

    service: str | None = None
    host: str | None = None
    version: str | None = None
    priority: str | None = None
    event_url: str | None = None
    occurred_at: datetime | None = None

    tags: list[str] = Field(default_factory=list)
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class DatadogAlertResponse(BaseModel):
    source_event_id: str
    processing_status: str
    severity: str | None = None
    internal_incident_id: str | None = None
    service_now_number: str | None = None
    investigation_id: str | None = None
    message: str
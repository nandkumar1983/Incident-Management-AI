from uuid import uuid4

from app.core.logger import logger
from app.domain.incident_model import Incident
from app.repository.incident_repository import (
    IncidentRepository,
)
from app.services.severity_service import (
    SeverityService,
)


class IncidentService:

    @staticmethod
    def create_incident(request) -> Incident:
        severity = SeverityService.predict(
            request.environment,
            request.description,
            request.application_name,
        )

        incident = Incident(
            incident_id=(
                f"INC-{uuid4().hex[:8].upper()}"
            ),
            title=request.title,
            description=request.description,
            application_name=request.application_name,
            environment=request.environment,
            severity=severity,
            status="OPEN",
            source_system="MANUAL",
            integration_status="NOT_REQUIRED",
        )

        saved_incident = IncidentRepository.save(
            incident
        )

        logger.info(
            "Incident created | incident_id=%s | "
            "application=%s | severity=%s",
            saved_incident.incident_id,
            saved_incident.application_name,
            saved_incident.severity,
        )

        return saved_incident

    @staticmethod
    def get_all_incidents() -> list[Incident]:
        return IncidentRepository.get_all()

    @staticmethod
    def get_incident_by_id(
        incident_id: str,
    ) -> Incident | None:
        return IncidentRepository.get_by_id(
            incident_id
        )

    @staticmethod
    def update_incident_status(
        incident_id: str,
        new_status: str,
    ) -> Incident | None:
        incident = IncidentRepository.update_status(
            incident_id,
            new_status,
        )

        if incident:
            logger.info(
                "Incident status updated | "
                "incident_id=%s | status=%s",
                incident_id,
                new_status,
            )

        return incident

    @staticmethod
    def map_servicenow_priority(
        severity: str,
    ) -> tuple[str, str]:

        mapping = {
            "Critical": ("1", "1"),
            "High": ("1", "2"),
            "Medium": ("2", "2"),
            "Low": ("3", "3"),
        }

        return mapping.get(
            severity,
            ("3", "3"),
        )
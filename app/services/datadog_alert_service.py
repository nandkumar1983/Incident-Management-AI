from uuid import uuid4

import httpx

from app.api.schemas import (
    DatadogAlertRequest,
    DatadogAlertResponse,
)
from app.clients.servicenow_client import (
    ServiceNowClient,
)
from app.core.config import (
    AGENT_AUTO_START,
    AGENT_ENABLED,
)
from app.core.logger import logger
from app.domain.incident_model import Incident
from app.repository.incident_repository import (
    IncidentRepository,
)
from app.services.incident_service import (
    IncidentService,
)
from app.services.investigation_service import (
    InvestigationService,
)
from app.services.severity_service import (
    SeverityService,
)


class DatadogAlertService:

    RECOVERY_STATES = {
        "OK",
        "RECOVERED",
        "RESOLVED",
    }

    @staticmethod
    async def process_alert(
        alert: DatadogAlertRequest,
    ) -> DatadogAlertResponse:

        existing_incident = (
            IncidentRepository.get_by_source_event_id(
                source_system="DATADOG",
                source_event_id=alert.event_id,
            )
        )

        if existing_incident:
            return DatadogAlertResponse(
                source_event_id=alert.event_id,
                processing_status="DUPLICATE",
                severity=existing_incident.severity,
                internal_incident_id=(
                    existing_incident.incident_id
                ),
                service_now_number=(
                    existing_incident
                    .service_now_number
                ),
                message="Alert already processed",
            )

        if (
            alert.alert_status.upper()
            in DatadogAlertService.RECOVERY_STATES
        ):
            return DatadogAlertResponse(
                source_event_id=alert.event_id,
                processing_status="RECOVERY_RECEIVED",
                message=(
                    "Recovery event received; "
                    "no new incident created"
                ),
            )

        severity = SeverityService.predict(
            environment=alert.environment,
            description=alert.alert_message,
            application_name=alert.application_name,
        )

        incident = Incident(
            incident_id=(
                f"INC-{uuid4().hex[:8].upper()}"
            ),
            title=alert.alert_title,
            description=alert.alert_message,
            application_name=alert.application_name,
            environment=alert.environment,
            severity=severity,
            status="OPEN",
            source_system="DATADOG",
            source_event_id=alert.event_id,
            datadog_monitor_id=alert.monitor_id,
            datadog_alert_status=alert.alert_status,
            service_name=alert.service,
            host_name=alert.host,
            deployed_version=alert.version,
            integration_status="PENDING",
            raw_payload=alert.model_dump(
                mode="json"
            ),
        )

        saved_incident = IncidentRepository.save(
            incident
        )

        impact, urgency = (
            IncidentService
            .map_servicenow_priority(
                severity
            )
        )

        snow_payload = {
            "short_description":
                alert.alert_title,
            "description": (
                f"{alert.alert_message}\n\n"
                f"Datadog event: {alert.event_id}\n"
                f"Monitor: {alert.monitor_id}\n"
                f"Application: "
                f"{alert.application_name}\n"
                f"Service: {alert.service}\n"
                f"Host: {alert.host}\n"
                f"Environment: "
                f"{alert.environment}\n"
                f"Version: {alert.version}\n"
                f"Event URL: {alert.event_url}"
            ),
            "impact": impact,
            "urgency": urgency,
            "category": "software",
            "contact_type": "monitoring",
            "correlation_id":
                alert.event_id,
        }

        service_now_number = None
        integration_status = "PENDING"

        try:
            snow_result = (
                await ServiceNowClient.create_incident(
                    snow_payload
                )
            )

            integration_status = snow_result[
                "integration_status"
            ]

            service_now_number = snow_result[
                "number"
            ]

            IncidentRepository.update_servicenow_result(
                incident_id=saved_incident.incident_id,
                integration_status=integration_status,
                service_now_sys_id=snow_result["sys_id"],
                service_now_number=snow_result["number"],
                integration_error=None,
            )

        except httpx.HTTPError as exc:
            integration_status = "FAILED"

            IncidentRepository.update_servicenow_result(
                incident_id=saved_incident.incident_id,
                integration_status="FAILED",
                service_now_sys_id=None,
                service_now_number=None,
                integration_error=str(exc),
            )

            logger.exception(
                "ServiceNow incident creation failed | "
                "incident_id=%s",
                saved_incident.incident_id,
            )

        investigation_id = None

        if AGENT_ENABLED and AGENT_AUTO_START:
            investigation_result = (
                await InvestigationService
                .investigate_incident(
                    saved_incident.incident_id
                )
            )

            investigation_id = (
                investigation_result
                .investigation_id
            )

        return DatadogAlertResponse(
            source_event_id=alert.event_id,
            processing_status=integration_status,
            severity=severity,
            internal_incident_id=(
                saved_incident.incident_id
            ),
            service_now_number=service_now_number,
            investigation_id=investigation_id,
            message=(
                "Datadog alert processed successfully"
            ),
        )
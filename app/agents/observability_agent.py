from app.api.agent_schemas import (
    EvidenceItem,
    ObservabilityResult,
)
from app.clients.datadog_client import DatadogClient
from app.core.config import AGENT_LOOKBACK_HOURS
from app.core.logger import logger


class ObservabilityAnalysisAgent:
    """Analyzes incident details and available Datadog evidence."""

    ERROR_TERMS = {
        "exception",
        "timeout",
        "timed out",
        "refused",
        "unavailable",
        "failed",
        "failure",
        "nullpointer",
        "connection",
        "database",
        "deadlock",
        "memory",
        "latency",
    }

    @staticmethod
    async def analyze(
        incident,
    ) -> ObservabilityResult:
        logger.info(
            "Observability analysis started | incident_id=%s",
            incident.incident_id,
        )

        error_signatures: list[str] = []
        affected_components: list[str] = []
        findings: list[str] = []
        evidence: list[EvidenceItem] = []

        description = incident.description or ""
        normalized_description = description.lower()

        detected_terms = sorted(
            {
                term
                for term
                in ObservabilityAnalysisAgent.ERROR_TERMS
                if term in normalized_description
            }
        )

        if detected_terms:
            error_signatures.extend(
                detected_terms
            )

            findings.append(
                "The incident description contains the "
                "following operational error indicators: "
                + ", ".join(detected_terms)
                + "."
            )

            evidence.append(
                EvidenceItem(
                    source="DATADOG",
                    evidence_type="ALERT_TEXT",
                    reference=incident.source_event_id,
                    summary=(
                        "The incident description contains "
                        "operational error indicators: "
                        + ", ".join(detected_terms)
                        + "."
                    ),
                    supports_hypothesis=True,
                    confidence=55.0,
                    raw_evidence={
                        "incident_id":
                            incident.incident_id,
                        "description":
                            incident.description,
                        "detected_terms":
                            detected_terms,
                    },
                )
            )

        else:
            findings.append(
                "No configured error terms were detected "
                "in the incident description."
            )

            evidence.append(
                EvidenceItem(
                    source="AGENT",
                    evidence_type="NO_ERROR_SIGNATURE",
                    reference=incident.incident_id,
                    summary=(
                        "No configured error signature was "
                        "identified in the incident description."
                    ),
                    supports_hypothesis=False,
                    confidence=40.0,
                    raw_evidence={
                        "description":
                            incident.description,
                    },
                )
            )

        if incident.application_name:
            affected_components.append(
                incident.application_name
            )

        if incident.service_name:
            affected_components.append(
                incident.service_name
            )

        if incident.host_name:
            affected_components.append(
                incident.host_name
            )

        # Remove duplicates while preserving order.
        affected_components = list(
            dict.fromkeys(affected_components)
        )

        if affected_components:
            findings.append(
                "Potentially affected components: "
                + ", ".join(affected_components)
                + "."
            )

        datadog_events = (
            await DatadogClient.search_events(
                service_name=incident.service_name,
                lookback_hours=AGENT_LOOKBACK_HOURS,
            )
        )

        if datadog_events:
            findings.append(
                (
                    f"{len(datadog_events)} related "
                    "Datadog event(s) were retrieved "
                    "within the configured lookback period."
                )
            )

            evidence.append(
                EvidenceItem(
                    source="DATADOG",
                    evidence_type="RELATED_EVENTS",
                    reference=incident.source_event_id,
                    summary=(
                        "Related Datadog events were found "
                        "for the affected service."
                    ),
                    supports_hypothesis=True,
                    confidence=65.0,
                    raw_evidence={
                        "event_count":
                            len(datadog_events),
                        "lookback_hours":
                            AGENT_LOOKBACK_HOURS,
                    },
                )
            )

        else:
            findings.append(
                "No additional Datadog events were available. "
                "This is expected when Datadog API integration "
                "is disabled or no related events exist."
            )

            evidence.append(
                EvidenceItem(
                    source="DATADOG",
                    evidence_type="NO_EXTERNAL_EVENTS",
                    reference=incident.source_event_id,
                    summary=(
                        "No additional Datadog events were "
                        "available for this investigation."
                    ),
                    supports_hypothesis=False,
                    confidence=30.0,
                    raw_evidence={
                        "lookback_hours":
                            AGENT_LOOKBACK_HOURS,
                    },
                )
            )

        result = ObservabilityResult(
            incident_id=incident.incident_id,
            service=incident.service_name,
            current_version=incident.deployed_version,
            error_signatures=error_signatures,
            affected_components=affected_components,
            findings=findings,
            evidence=evidence,
        )

        logger.info(
            "Observability analysis completed | "
            "incident_id=%s | "
            "error_signatures=%s | "
            "affected_components=%s | "
            "evidence_count=%s",
            incident.incident_id,
            len(error_signatures),
            len(affected_components),
            len(evidence),
        )

        return result
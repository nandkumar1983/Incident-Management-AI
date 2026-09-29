from app.agents.evidence_validator import EvidenceValidator
from app.api.agent_schemas import (
    EvidenceItem,
    ObservabilityResult,
    RegressionAnalysisResult,
)
from app.core.config import PREVIOUS_INCIDENT_LOOKBACK_DAYS
from app.core.logger import logger
from app.repository.incident_repository import IncidentRepository


class RegressionAnalysisAgent:
    """Analyzes whether an incident resembles a previous incident."""

    @staticmethod
    async def analyze(
        incident,
        observability_result: ObservabilityResult,
    ) -> tuple[
        RegressionAnalysisResult,
        list[EvidenceItem],
    ]:
        logger.info(
            "Regression analysis started | incident_id=%s",
            incident.incident_id,
        )

        evidence: list[EvidenceItem] = []
        findings: list[str] = []

        previous_incidents = (
            IncidentRepository.find_similar_incidents(
                incident=incident,
                lookback_days=PREVIOUS_INCIDENT_LOOKBACK_DAYS,
            )
        )

        previous_incident_id: str | None = None
        previous_fix_reference: str | None = None
        similar_error_found = False

        current_words = {
            word.strip(".,:;()[]{}")
            for word in incident.description.lower().split()
            if len(word.strip(".,:;()[]{}")) >= 5
        }

        for previous_incident in previous_incidents:
            previous_words = {
                word.strip(".,:;()[]{}")
                for word in previous_incident.description.lower().split()
                if len(word.strip(".,:;()[]{}")) >= 5
            }

            matching_words = current_words.intersection(
                previous_words
            )

            if len(matching_words) < 2:
                continue

            previous_incident_id = (
                previous_incident.incident_id
            )
            similar_error_found = True

            findings.append(
                (
                    "Similar previous incident found: "
                    f"{previous_incident_id}. "
                    "Matching terms: "
                    + ", ".join(
                        sorted(matching_words)[:10]
                    )
                )
            )

            evidence.append(
                EvidenceItem(
                    source="DATABASE",
                    evidence_type="SIMILAR_INCIDENT",
                    reference=previous_incident_id,
                    summary=(
                        "A previous incident contains multiple "
                        "matching error terms."
                    ),
                    supports_hypothesis=True,
                    confidence=min(
                        85.0,
                        45.0 + len(matching_words) * 8.0,
                    ),
                    raw_evidence={
                        "matching_terms": sorted(
                            matching_words
                        ),
                        "previous_title":
                            previous_incident.title,
                        "previous_description":
                            previous_incident.description,
                        "previous_severity":
                            previous_incident.severity,
                        "previous_status":
                            previous_incident.status,
                    },
                )
            )

            break

        if not similar_error_found:
            findings.append(
                "No sufficiently similar previous incident "
                "was found within the configured lookback period."
            )

            evidence.append(
                EvidenceItem(
                    source="DATABASE",
                    evidence_type="NO_SIMILAR_INCIDENT",
                    reference=None,
                    summary=(
                        "No similar previous incident was found "
                        "within the configured lookback period."
                    ),
                    supports_hypothesis=False,
                    confidence=60.0,
                    raw_evidence={
                        "lookback_days":
                            PREVIOUS_INCIDENT_LOOKBACK_DAYS,
                        "candidate_count":
                            len(previous_incidents),
                    },
                )
            )

        confidence = (
            EvidenceValidator.calculate_confidence(
                evidence
            )
        )

        regression_related = (
            similar_error_found
            and confidence >= 60.0
        )

        logger.info(
            "Regression analysis completed | "
            "incident_id=%s | "
            "similar_error_found=%s | "
            "confidence=%s",
            incident.incident_id,
            similar_error_found,
            confidence,
        )

        result = RegressionAnalysisResult(
            regression_related=regression_related,
            confidence=confidence,
            previous_incident_id=previous_incident_id,
            previous_fix_reference=previous_fix_reference,
            similar_error_found=similar_error_found,
            findings=findings,
        )

        return result, evidence
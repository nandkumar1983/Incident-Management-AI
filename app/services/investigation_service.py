from app.agents.investigation_agent import (
    IncidentInvestigationAgent,
)
from app.api.agent_schemas import InvestigationResult
from app.clients.servicenow_client import (
    ServiceNowClient,
)
from app.core.config import HUMAN_APPROVAL_REQUIRED
from app.core.logger import logger
from app.domain.evidence_model import (
    InvestigationEvidence,
)
from app.domain.investigation_model import (
    IncidentInvestigation,
)
from app.repository.incident_repository import (
    IncidentRepository,
)
from app.repository.investigation_repository import (
    InvestigationRepository,
)


class InvestigationService:

    @staticmethod
    async def investigate_incident(
        incident_id: str,
    ) -> InvestigationResult:

        incident = IncidentRepository.get_by_id(
            incident_id
        )

        if incident is None:
            raise LookupError(
                f"Incident '{incident_id}' was not found"
            )

        investigation = IncidentInvestigation(
            incident_id=incident.incident_id,
            service_now_number=(
                incident.service_now_number
            ),
            investigation_status="STARTED",
            requires_human_approval=(
                HUMAN_APPROVAL_REQUIRED
            ),
            approval_status="PENDING",
        )

        saved_investigation = (
            InvestigationRepository.create(
                investigation
            )
        )

        result = (
            await IncidentInvestigationAgent
            .investigate(incident)
        )

        result.investigation_id = str(
            saved_investigation.investigation_id
        )

        for item in result.evidence:
            InvestigationRepository.save_evidence(
                InvestigationEvidence(
                    investigation_id=(
                        saved_investigation
                        .investigation_id
                    ),
                    evidence_type=item.evidence_type,
                    source_system=item.source,
                    source_reference=item.reference,
                    summary=item.summary,
                    supports_hypothesis=(
                        item.supports_hypothesis
                    ),
                    confidence=item.confidence,
                    raw_evidence=item.raw_evidence,
                )
            )

        fix_recommendation = (
            result.fix_recommendation
        )

        InvestigationRepository.complete(
            investigation_id=(
                saved_investigation.investigation_id
            ),
            analysis_summary=(
                result.investigation_summary
            ),
            probable_root_cause=(
                result.probable_root_cause
            ),
            suspected_component=(
                result.affected_component
            ),
            release_related=(
                result.release_analysis
                .release_related
            ),
            release_confidence=(
                result.release_analysis
                .confidence
            ),
            regression_related=(
                result.regression_analysis
                .regression_related
            ),
            regression_confidence=(
                result.regression_analysis
                .confidence
            ),
            recommended_mitigation="\n".join(
                result.immediate_mitigation
            ),
            recommended_code_fix=(
                fix_recommendation.approach
                if fix_recommendation
                else None
            ),
            recommended_tests={
                "tests": (
                    fix_recommendation
                    .tests_required
                    if fix_recommendation
                    else []
                )
            },
            analysis_payload=result.model_dump(
                mode="json"
            ),
        )

        work_note = (
            "AI INCIDENT INVESTIGATION\n"
            "=========================\n"
            f"Internal incident: {incident.incident_id}\n"
            f"Investigation ID: {result.investigation_id}\n"
            f"Investigation status: "
            f"{result.investigation_status}\n\n"

            "ANALYSIS SUMMARY\n"
            "----------------\n"
            f"{result.investigation_summary}\n\n"

            "PROBABLE ROOT CAUSE\n"
            "-------------------\n"
            f"{result.probable_root_cause}\n\n"

            "AFFECTED COMPONENT\n"
            "------------------\n"
            f"{result.affected_component}\n\n"

            "RELEASE CORRELATION\n"
            "-------------------\n"
            f"Release related: "
            f"{result.release_analysis.release_related}\n"
            f"Confidence: "
            f"{result.release_analysis.confidence}%\n"
            f"Version: "
            f"{result.release_analysis.current_version}\n"
            f"Commit: "
            f"{result.release_analysis.commit_sha}\n"
            f"Conclusion: "
            f"{result.release_analysis.conclusion}\n\n"

            "PREVIOUS-INCIDENT REGRESSION CHECK\n"
            "----------------------------------\n"
            f"Regression related: "
            f"{result.regression_analysis.regression_related}\n"
            f"Confidence: "
            f"{result.regression_analysis.confidence}%\n"
            f"Previous incident: "
            f"{result.regression_analysis.previous_incident_id}\n\n"

            "IMMEDIATE MITIGATION\n"
            "--------------------\n"
            + "\n".join(
                f"- {item}"
                for item
                in result.immediate_mitigation
            )
            + "\n\n"

            "RECOMMENDED CODE FIX\n"
            "--------------------\n"
            f"{result.fix_recommendation.approach}\n\n"

            "RECOMMENDED TESTS\n"
            "-----------------\n"
            + "\n".join(
                f"- {test}"
                for test
                in result.fix_recommendation.tests_required
            )
            + "\n\n"

            "RISKS\n"
            "-----\n"
            + "\n".join(
                f"- {risk}"
                for risk
                in result.fix_recommendation.risks
            )
            + "\n\n"

            "APPROVAL\n"
            "--------\n"
            "Human approval required: TRUE\n"
            "Approval status: PENDING\n"
            "No production change has been performed."
        )

        await ServiceNowClient.add_work_note(
            incident.service_now_sys_id,
            work_note,
        )

        logger.info(
            "Investigation persisted | "
            "investigation_id=%s",
            result.investigation_id,
        )

        return result
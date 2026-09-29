from app.agents.code_fix_agent import (
    CodeFixRecommendationAgent,
)
from app.agents.observability_agent import (
    ObservabilityAnalysisAgent,
)
from app.agents.regression_analysis_agent import (
    RegressionAnalysisAgent,
)
from app.agents.release_correlation_agent import (
    ReleaseCorrelationAgent,
)
from app.api.agent_schemas import InvestigationResult
from app.core.config import HUMAN_APPROVAL_REQUIRED
from app.core.logger import logger


class IncidentInvestigationAgent:

    @staticmethod
    async def investigate(
        incident,
    ) -> InvestigationResult:

        logger.info(
            "Agent investigation started | incident_id=%s",
            incident.incident_id,
        )

        observability_result = (
            await ObservabilityAnalysisAgent.analyze(
                incident
            )
        )

        (
            release_result,
            release_evidence,
        ) = await ReleaseCorrelationAgent.analyze(
            incident=incident,
            observability_result=observability_result,
        )

        (
            regression_result,
            regression_evidence,
        ) = await RegressionAnalysisAgent.analyze(
            incident=incident,
            observability_result=observability_result,
        )

        fix_recommendation = (
            await CodeFixRecommendationAgent.recommend(
                incident=incident,
                observability_result=observability_result,
                release_result=release_result,
                regression_result=regression_result,
            )
        )

        all_evidence = (
            observability_result.evidence
            + release_evidence
            + regression_evidence
        )

        probable_root_cause = None

        if release_result.release_related:
            probable_root_cause = (
                "Potential regression associated with a "
                "recent code or deployment change."
            )

        elif regression_result.regression_related:
            probable_root_cause = (
                "Potential recurrence of a previously "
                "observed incident pattern."
            )

        elif observability_result.error_signatures:
            probable_root_cause = (
                "Operational failure associated with: "
                + ", ".join(
                    observability_result.error_signatures
                )
            )

        investigation_status = (
            "COMPLETED"
            if all_evidence
            else "INSUFFICIENT_EVIDENCE"
        )

        investigation_summary = (
            f"Incident {incident.incident_id} was analyzed "
            "using observability, release-correlation and "
            "previous-incident evidence. "
            f"Release confidence is "
            f"{release_result.confidence}%. "
            f"Regression confidence is "
            f"{regression_result.confidence}%."
        )

        immediate_mitigation = [
            "Validate current customer and business impact.",
            "Confirm whether the issue affects all service instances.",
            "Review recent deployment and change activity.",
            "Use the approved rollback or workaround only after human approval.",
        ]

        logger.info(
            "Agent investigation completed | "
            "incident_id=%s | release_confidence=%s | "
            "regression_confidence=%s",
            incident.incident_id,
            release_result.confidence,
            regression_result.confidence,
        )

        return InvestigationResult(
            incident_id=incident.incident_id,
            investigation_status=investigation_status,
            investigation_summary=investigation_summary,
            probable_root_cause=probable_root_cause,
            affected_component=(
                fix_recommendation.component
            ),
            release_analysis=release_result,
            regression_analysis=regression_result,
            fix_recommendation=fix_recommendation,
            immediate_mitigation=immediate_mitigation,
            evidence=all_evidence,
            human_approval_required=(
                HUMAN_APPROVAL_REQUIRED
            ),
            approval_status="PENDING",
        )
from datetime import datetime, timezone
from uuid import UUID

from app.core.database import SessionLocal
from app.domain.evidence_model import InvestigationEvidence
from app.domain.investigation_model import IncidentInvestigation


class InvestigationRepository:

    @staticmethod
    def create(
        investigation: IncidentInvestigation,
    ) -> IncidentInvestigation:
        database_session = SessionLocal()

        try:
            database_session.add(investigation)
            database_session.commit()
            database_session.refresh(investigation)
            return investigation

        except Exception:
            database_session.rollback()
            raise

        finally:
            database_session.close()

    @staticmethod
    def get_by_id(
        investigation_id: UUID,
    ) -> IncidentInvestigation | None:
        database_session = SessionLocal()

        try:
            return (
                database_session
                .query(IncidentInvestigation)
                .filter(
                    IncidentInvestigation.investigation_id
                    == investigation_id
                )
                .first()
            )

        finally:
            database_session.close()

    @staticmethod
    def get_latest_for_incident(
        incident_id: str,
    ) -> IncidentInvestigation | None:
        database_session = SessionLocal()

        try:
            return (
                database_session
                .query(IncidentInvestigation)
                .filter(
                    IncidentInvestigation.incident_id
                    == incident_id
                )
                .order_by(
                    IncidentInvestigation.created_at.desc()
                )
                .first()
            )

        finally:
            database_session.close()

    @staticmethod
    def save_evidence(
        evidence: InvestigationEvidence,
    ) -> InvestigationEvidence:
        database_session = SessionLocal()

        try:
            database_session.add(evidence)
            database_session.commit()
            database_session.refresh(evidence)
            return evidence

        except Exception:
            database_session.rollback()
            raise

        finally:
            database_session.close()

    @staticmethod
    def complete(
        investigation_id: UUID,
        analysis_summary: str,
        probable_root_cause: str | None,
        suspected_component: str | None,
        release_related: bool,
        release_confidence: float,
        regression_related: bool,
        regression_confidence: float,
        recommended_mitigation: str,
        recommended_code_fix: str | None,
        recommended_tests: dict,
        analysis_payload: dict,
    ) -> IncidentInvestigation | None:
        database_session = SessionLocal()

        try:
            investigation = (
                database_session
                .query(IncidentInvestigation)
                .filter(
                    IncidentInvestigation.investigation_id
                    == investigation_id
                )
                .first()
            )

            if investigation is None:
                return None

            investigation.investigation_status = "COMPLETED"
            investigation.analysis_summary = analysis_summary
            investigation.probable_root_cause = (
                probable_root_cause
            )
            investigation.suspected_component = (
                suspected_component
            )
            investigation.release_related = release_related
            investigation.release_confidence = (
                release_confidence
            )
            investigation.regression_related = (
                regression_related
            )
            investigation.regression_confidence = (
                regression_confidence
            )
            investigation.recommended_mitigation = (
                recommended_mitigation
            )
            investigation.recommended_code_fix = (
                recommended_code_fix
            )
            investigation.recommended_tests = (
                recommended_tests
            )
            investigation.analysis_payload = analysis_payload
            investigation.completed_at = datetime.now(
                timezone.utc
            )

            database_session.commit()
            database_session.refresh(investigation)

            return investigation

        except Exception:
            database_session.rollback()
            raise

        finally:
            database_session.close()
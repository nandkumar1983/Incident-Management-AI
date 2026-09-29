from datetime import datetime, timedelta, timezone

from sqlalchemy import or_

from app.core.database import SessionLocal
from app.domain.incident_model import Incident


class IncidentRepository:

    @staticmethod
    def save(incident: Incident) -> Incident:
        database_session = SessionLocal()

        try:
            database_session.add(incident)
            database_session.commit()
            database_session.refresh(incident)
            return incident

        except Exception:
            database_session.rollback()
            raise

        finally:
            database_session.close()

    @staticmethod
    def get_all() -> list[Incident]:
        database_session = SessionLocal()

        try:
            return (
                database_session.query(Incident)
                .order_by(Incident.created_at.desc())
                .all()
            )

        finally:
            database_session.close()

    @staticmethod
    def get_by_id(
        incident_id: str,
    ) -> Incident | None:
        database_session = SessionLocal()

        try:
            return (
                database_session.query(Incident)
                .filter(
                    Incident.incident_id == incident_id
                )
                .first()
            )

        finally:
            database_session.close()

    @staticmethod
    def get_by_source_event_id(
        source_system: str,
        source_event_id: str,
    ) -> Incident | None:
        database_session = SessionLocal()

        try:
            return (
                database_session.query(Incident)
                .filter(
                    Incident.source_system == source_system,
                    Incident.source_event_id == source_event_id,
                )
                .first()
            )

        finally:
            database_session.close()

    @staticmethod
    def find_similar_incidents(
        incident: Incident,
        lookback_days: int,
    ) -> list[Incident]:
        database_session = SessionLocal()

        cutoff_time = (
            datetime.now(timezone.utc)
            - timedelta(days=lookback_days)
        )

        try:
            return (
                database_session.query(Incident)
                .filter(
                    Incident.incident_id
                    != incident.incident_id,
                    Incident.created_at >= cutoff_time,
                    or_(
                        Incident.application_name
                        == incident.application_name,
                        Incident.service_name
                        == incident.service_name,
                        Incident.title.ilike(
                            f"%{incident.title[:40]}%"
                        ),
                    ),
                )
                .order_by(Incident.created_at.desc())
                .limit(20)
                .all()
            )

        finally:
            database_session.close()

    @staticmethod
    def update_status(
        incident_id: str,
        new_status: str,
    ) -> Incident | None:
        database_session = SessionLocal()

        try:
            incident = (
                database_session.query(Incident)
                .filter(
                    Incident.incident_id == incident_id
                )
                .first()
            )

            if incident is None:
                return None

            incident.status = new_status

            database_session.commit()
            database_session.refresh(incident)

            return incident

        except Exception:
            database_session.rollback()
            raise

        finally:
            database_session.close()

    @staticmethod
    def update_servicenow_result(
        incident_id: str,
        integration_status: str,
        service_now_sys_id: str | None,
        service_now_number: str | None,
        integration_error: str | None,
    ) -> Incident | None:
        database_session = SessionLocal()

        try:
            incident = (
                database_session.query(Incident)
                .filter(
                    Incident.incident_id == incident_id
                )
                .first()
            )

            if incident is None:
                return None

            incident.integration_status = integration_status
            incident.service_now_sys_id = service_now_sys_id
            incident.service_now_number = service_now_number
            incident.integration_error = integration_error

            database_session.commit()
            database_session.refresh(incident)

            return incident

        except Exception:
            database_session.rollback()
            raise

        finally:
            database_session.close()
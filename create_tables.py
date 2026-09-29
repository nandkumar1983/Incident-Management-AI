from app.core.database import (
    Base,
    engine,
)

from app.domain.evidence_model import (
    InvestigationEvidence,
)
from app.domain.incident_model import Incident
from app.domain.investigation_model import (
    IncidentInvestigation,
)


def create_tables() -> None:
    Base.metadata.create_all(
        bind=engine
    )

    print(
        "Database tables created or verified successfully."
    )


if __name__ == "__main__":
    create_tables()
from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from app.api.agent_schemas import InvestigationResult
from app.core.logger import logger
from app.services.investigation_service import (
    InvestigationService,
)


router = APIRouter(
    prefix="/api/v1/investigations",
    tags=["Incident Investigation Agent"],
)


@router.post(
    "/incidents/{incident_id}",
    response_model=InvestigationResult,
)
async def investigate_incident(
    incident_id: str,
):
    try:
        return (
            await InvestigationService
            .investigate_incident(
                incident_id
            )
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except Exception:
        logger.exception(
            "Incident investigation failed | "
            "incident_id=%s",
            incident_id,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Incident investigation failed. "
                "Review the application logs for details."
            ),
        )
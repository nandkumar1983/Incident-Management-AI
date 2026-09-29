from fastapi import (
    FastAPI,
    HTTPException,
    status,
)

from app.api.datadog_routes import (
    router as datadog_router,
)
from app.api.investigation_routes import (
    router as investigation_router,
)
from app.api.schemas import (
    IncidentRequest,
    IncidentResponse,
    IncidentStatusUpdate,
)
from app.core.config import (
    APP_NAME,
    APP_VERSION,
)
from app.services.incident_service import (
    IncidentService,
)


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "Datadog-driven intelligent incident management, "
        "ServiceNow integration, release correlation, "
        "regression analysis and code-fix recommendations."
    ),
)

# Routers
app.include_router(datadog_router)
app.include_router(investigation_router)


def build_incident_response(
    incident,
) -> IncidentResponse:
    return IncidentResponse(
        incident_id=incident.incident_id,
        title=incident.title,
        description=incident.description,
        application_name=incident.application_name,
        environment=incident.environment,
        severity=incident.severity,
        status=incident.status,
        source_system=incident.source_system,
        service_now_number=incident.service_now_number,
        created_at=incident.created_at,
    )


# ---------------------------------------------------
# Platform Health
# ---------------------------------------------------

@app.get(
    "/",
    tags=["Platform Health"],
)
async def home():
    return {
        "application": APP_NAME,
        "version": APP_VERSION,
        "status": "RUNNING",
    }


# ---------------------------------------------------
# Incident Management
# ---------------------------------------------------

@app.post(
    "/incidents",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Incident Management"],
)
async def create_incident(
    request: IncidentRequest,
):
    incident = IncidentService.create_incident(
        request
    )

    return build_incident_response(
        incident
    )


@app.get(
    "/incidents",
    response_model=list[IncidentResponse],
    tags=["Incident Management"],
)
async def get_incidents():
    incidents = (
        IncidentService.get_all_incidents()
    )

    return [
        build_incident_response(incident)
        for incident in incidents
    ]


@app.get(
    "/incidents/{incident_id}",
    response_model=IncidentResponse,
    tags=["Incident Management"],
)
async def get_incident(
    incident_id: str,
):
    incident = (
        IncidentService.get_incident_by_id(
            incident_id
        )
    )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    return build_incident_response(
        incident
    )


@app.put(
    "/incidents/{incident_id}/status",
    response_model=IncidentResponse,
    tags=["Incident Management"],
)
async def update_incident_status(
    incident_id: str,
    request: IncidentStatusUpdate,
):
    incident = (
        IncidentService.update_incident_status(
            incident_id,
            request.status,
        )
    )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    return build_incident_response(
        incident
    )
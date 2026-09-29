from fastapi import (
    APIRouter,
    Header,
    HTTPException,
    status,
)

from app.api.schemas import (
    DatadogAlertRequest,
    DatadogAlertResponse,
)
from app.core.config import DATADOG_WEBHOOK_TOKEN
from app.services.datadog_alert_service import (
    DatadogAlertService,
)


router = APIRouter(
    prefix="/api/v1/webhooks",
    tags=["Datadog Integration"],
)


@router.post(
    "/datadog",
    response_model=DatadogAlertResponse,
)
async def receive_datadog_alert(
    alert: DatadogAlertRequest,
    x_webhook_token: str = Header(
        alias="X-Webhook-Token",
    ),
):

    if x_webhook_token != DATADOG_WEBHOOK_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Datadog webhook token",
        )

    return await DatadogAlertService.process_alert(
        alert
    )
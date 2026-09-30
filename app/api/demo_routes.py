import traceback
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import (
    APIRouter,
    Header,
    HTTPException,
    status,
)

from app.api.schemas import (
    DatadogAlertRequest,
    FaultInjectionRequest,
    FaultInjectionResponse,
)
from app.clients.datadog_client import DatadogClient
from app.core.config import (
    DEMO_MODE,
    FAULT_API_TOKEN,
    FAULT_INJECTION_ENABLED,
)
from app.core.logger import logger
from app.services.datadog_alert_service import (
    DatadogAlertService,
)
from app.services.demo_payment_service import (
    DemoPaymentService,
)


router = APIRouter(
    prefix="/api/v1/demo",
    tags=["Controlled Fault Demonstration"],
)


@router.post(
    "/payment-profile-failure",
    response_model=FaultInjectionResponse,
    operation_id="payment_profile_failure_demo",
)
async def trigger_payment_profile_failure(
    request: FaultInjectionRequest,
    x_fault_token: str = Header(
        alias="X-Fault-Token",
    ),
):
    if not DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo mode is disabled",
        )

    if not FAULT_INJECTION_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Fault injection is disabled",
        )

    if x_fault_token != FAULT_API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid fault-injection token",
        )

    scenario_id = (
        f"FAULT-{uuid4().hex[:12].upper()}"
    )

    try:
        payment_result = (
            DemoPaymentService.authorize_payment(
                customer_id=request.customer_id,
                amount=request.amount,
                inject_fault=request.inject_fault,
            )
        )

        return FaultInjectionResponse(
            scenario=scenario_id,
            fault_triggered=False,
            datadog_event_status="NOT_REQUIRED",
            human_approval_required=True,
        )

    except Exception as exc:
        error_type = type(exc).__name__
        error_message = str(exc)
        stack_trace = traceback.format_exc()

        logger.exception(
            "Controlled payment fault triggered | "
            "scenario_id=%s | customer_id=%s",
            scenario_id,
            request.customer_id,
        )

        datadog_title = (
            "Payment authorization failed: "
            "customer profile response was null"
        )

        datadog_message = (
            "A controlled development fault occurred.\n\n"
            f"Scenario ID: {scenario_id}\n"
            f"Error type: {error_type}\n"
            f"Error message: {error_message}\n"
            "Application: Payments\n"
            "Service: payment-api\n"
            "Environment: Development\n"
            "Version: demo-null-profile-1.0.0\n\n"
            f"Stack trace:\n{stack_trace}"
        )

        try:
            datadog_result = (
                await DatadogClient.post_alert_event(
                    title=datadog_title,
                    message=datadog_message,
                    aggregation_key=scenario_id,
                    tags=[
                        "env:development",
                        "application:payments",
                        "service:payment-api",
                    ],
                )
            )
        except Exception as exc:
            logger.warning(
                "Datadog failed. Running simulation mode. Error=%s",
                exc,
            )

            datadog_result = {
                "status": "SIMULATED",
                "event_id": scenario_id,
                "event_url": None,
            }

        source_event_id = (
            datadog_result.get("event_id")
            or scenario_id
        )

        alert_request = DatadogAlertRequest(
            event_id=source_event_id,
            monitor_id="DEMO-PAYMENT-PROFILE",
            monitor_name=(
                "Controlled payment profile failure"
            ),
            alert_status="ALERT",
            alert_title=datadog_title,
            alert_message=datadog_message,
            application_name="Payments",
            environment="Development",
            service="payment-api",
            host="localhost",
            version="demo-null-profile-1.0.0",
            priority="P2",
            event_url=datadog_result.get(
                "event_url"
            ),
            occurred_at=datetime.now(
                timezone.utc
            ),
            tags=[
                "env:development",
                "service:payment-api",
                "version:demo-null-profile-1.0.0",
                f"fault_id:{scenario_id}",
            ],
            raw_payload={
                "scenario_id": scenario_id,
                "error_type": error_type,
                "error_message": error_message,
                "stack_trace": stack_trace,
                "customer_id":
                    request.customer_id,
                "amount": request.amount,
                "controlled_test": True,
            },
        )

        processing_result = (
            await DatadogAlertService.process_alert(
                alert_request
            )
        )

        return FaultInjectionResponse(
            scenario=scenario_id,
            fault_triggered=True,
            error_type=error_type,
            error_message=error_message,
            datadog_event_status=(
                datadog_result["status"]
            ),
            datadog_event_id=(
                datadog_result.get("event_id")
            ),
            internal_incident_id=(
                processing_result
                .internal_incident_id
            ),
            service_now_number=(
                processing_result
                .service_now_number
            ),
            investigation_id=(
                processing_result
                .investigation_id
            ),
            investigation_status=(
                "COMPLETED"
                if processing_result
                .investigation_id
                else None
            ),
            human_approval_required=True,
        )
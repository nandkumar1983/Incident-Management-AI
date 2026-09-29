from typing import Any

import httpx

from app.core.config import (
    SERVICENOW_ENABLED,
    SERVICENOW_INSTANCE,
    SERVICENOW_PASSWORD,
    SERVICENOW_TIMEOUT_SECONDS,
    SERVICENOW_USERNAME,
)
from app.core.logger import logger


class ServiceNowClient:

    INCIDENT_TABLE_PATH = "/api/now/table/incident"

    @staticmethod
    async def create_incident(
        payload: dict[str, Any],
    ) -> dict[str, Any]:

        if not SERVICENOW_ENABLED:
            logger.warning(
                "ServiceNow disabled, incident creation skipped"
            )

            return {
                "integration_status": "SKIPPED",
                "sys_id": None,
                "number": None,
            }

        url = (
            f"{SERVICENOW_INSTANCE}"
            f"{ServiceNowClient.INCIDENT_TABLE_PATH}"
        )

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(
            timeout=SERVICENOW_TIMEOUT_SECONDS,
        ) as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload,
                auth=(
                    SERVICENOW_USERNAME,
                    SERVICENOW_PASSWORD,
                ),
            )

            response.raise_for_status()

            result = response.json().get(
                "result",
                {},
            )

            return {
                "integration_status": "CREATED",
                "sys_id": result.get("sys_id"),
                "number": result.get("number"),
            }

    @staticmethod
    async def add_work_note(
        service_now_sys_id: str | None,
        note: str,
    ) -> None:

        if (
            not SERVICENOW_ENABLED
            or not service_now_sys_id
        ):
            return

        url = (
            f"{SERVICENOW_INSTANCE}"
            f"{ServiceNowClient.INCIDENT_TABLE_PATH}"
            f"/{service_now_sys_id}"
        )

        payload = {
            "work_notes": note,
        }

        async with httpx.AsyncClient(
            timeout=SERVICENOW_TIMEOUT_SECONDS,
        ) as client:
            response = await client.patch(
                url,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                json=payload,
                auth=(
                    SERVICENOW_USERNAME,
                    SERVICENOW_PASSWORD,
                ),
            )

            response.raise_for_status()
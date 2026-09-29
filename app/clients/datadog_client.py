from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.core.config import (
    DATADOG_API_BASE_URL,
    DATADOG_API_KEY,
    DATADOG_APPLICATION_KEY,
    DATADOG_ENABLED,
)
from app.core.logger import logger


class DatadogClient:

    @staticmethod
    def _headers() -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "DD-API-KEY": DATADOG_API_KEY,
            "DD-APPLICATION-KEY":
                DATADOG_APPLICATION_KEY,
        }

    @staticmethod
    async def search_events(
        service_name: str | None,
        lookback_hours: int,
    ) -> list[dict[str, Any]]:

        if not DATADOG_ENABLED:
            logger.info(
                "Datadog API disabled, returning no external events"
            )
            return []

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(
            hours=lookback_hours
        )

        query = "*"

        if service_name:
            query = f"service:{service_name}"

        payload = {
            "filter": {
                "from": start_time.isoformat(),
                "to": end_time.isoformat(),
                "query": query,
            },
            "page": {
                "limit": 50,
            },
            "sort": "timestamp",
        }

        url = (
            f"{DATADOG_API_BASE_URL}"
            f"/api/v2/events/search"
        )

        async with httpx.AsyncClient(
            timeout=30,
        ) as client:
            response = await client.post(
                url,
                headers=DatadogClient._headers(),
                json=payload,
            )

            response.raise_for_status()

            return response.json().get(
                "data",
                [],
            )
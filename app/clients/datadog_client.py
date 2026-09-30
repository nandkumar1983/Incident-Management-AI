from datetime import datetime, timedelta, timezone
from typing import Any
import httpx
from app.core.config import (
    DATADOG_API_BASE_URL,
    DATADOG_API_KEY,
    DATADOG_APPLICATION_KEY,
    DATADOG_ENABLED,
    DATADOG_EVENT_INTAKE_URL,
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

            

            if response.status_code >= 400:
                logger.error(
                    "Datadog event search failed | status=%s | response=%s",
                    response.status_code,
                    response.text,
                )
                return []

            return response.json().get(
                "data",
                [],
            )

    @staticmethod
    async def post_alert_event(
        title: str,
        message: str,
        aggregation_key: str,
        tags: list[str],
    ) -> dict[str, Any]:

        if not DATADOG_ENABLED:
            logger.warning(
                "Datadog API is disabled; event publication skipped"
            )

            return {
                "status": "SKIPPED",
                "event_id": None,
                "event_url": None,
            }

        if not DATADOG_API_KEY:
            raise RuntimeError(
                "DATADOG_API_KEY is not configured"
            )

        event_url = (
            f"{DATADOG_EVENT_INTAKE_URL}"
            "/api/v2/events"
        )

        payload = {
            "data": {
                "type": "event",
                "attributes": {
                    "category": "alert",
                    "title": title,
                    "message": message,
                    "aggregation_key": aggregation_key,
                    "tags": tags,
                },
            }
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "DD-API-KEY": DATADOG_API_KEY,
        }

        if DATADOG_APPLICATION_KEY:
            headers["DD-APPLICATION-KEY"] = (
                DATADOG_APPLICATION_KEY
            )

        async with httpx.AsyncClient(
            timeout=30,
        ) as client:
            response = await client.post(
                event_url,
                headers=headers,
                json=payload,
            )

            response.raise_for_status()

            response_data = response.json()

            data = response_data.get(
                "data",
                {},
            )

            attributes = data.get(
                "attributes",
                {},
            )

            links = response_data.get(
                "links",
                {},
            )

            generated_event_id = (
                data.get("id")
                or attributes.get("id")
            )

            logger.info(
                "Datadog alert event published | "
                "event_id=%s | title=%s",
                generated_event_id,
                title,
            )

            return {
                "status": "CREATED",
                "event_id": generated_event_id,
                "event_url": links.get("self"),
                "raw_response": response_data,
            }
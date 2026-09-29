from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.core.config import (
    GITHUB_API_URL,
    GITHUB_DEFAULT_BRANCH,
    GITHUB_ENABLED,
    GITHUB_OWNER,
    GITHUB_REPOSITORY,
    GITHUB_TOKEN,
)
from app.core.logger import logger


class GitHubClient:

    @staticmethod
    def _headers() -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        if GITHUB_TOKEN:
            headers["Authorization"] = (
                f"Bearer {GITHUB_TOKEN}"
            )

        return headers

    @staticmethod
    async def get_recent_commits(
        lookback_hours: int,
    ) -> list[dict[str, Any]]:

        if not GITHUB_ENABLED:
            logger.info(
                "GitHub API disabled, returning no commits"
            )
            return []

        since_time = (
            datetime.now(timezone.utc)
            - timedelta(hours=lookback_hours)
        )

        url = (
            f"{GITHUB_API_URL}/repos/"
            f"{GITHUB_OWNER}/{GITHUB_REPOSITORY}/commits"
        )

        params = {
            "sha": GITHUB_DEFAULT_BRANCH,
            "since": since_time.isoformat(),
            "per_page": 50,
        }

        async with httpx.AsyncClient(
            timeout=30,
        ) as client:
            response = await client.get(
                url,
                headers=GitHubClient._headers(),
                params=params,
            )

            response.raise_for_status()
            return response.json()

    @staticmethod
    async def get_commit_details(
        commit_sha: str,
    ) -> dict[str, Any]:

        if not GITHUB_ENABLED:
            return {}

        url = (
            f"{GITHUB_API_URL}/repos/"
            f"{GITHUB_OWNER}/{GITHUB_REPOSITORY}"
            f"/commits/{commit_sha}"
        )

        async with httpx.AsyncClient(
            timeout=30,
        ) as client:
            response = await client.get(
                url,
                headers=GitHubClient._headers(),
            )

            response.raise_for_status()
            return response.json()
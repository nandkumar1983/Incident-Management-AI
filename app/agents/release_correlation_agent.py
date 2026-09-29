from app.agents.evidence_validator import EvidenceValidator
from app.api.agent_schemas import (
    EvidenceItem,
    ObservabilityResult,
    ReleaseAnalysisResult,
)
from app.clients.github_client import GitHubClient
from app.core.config import RELEASE_LOOKBACK_HOURS
from app.core.logger import logger


class ReleaseCorrelationAgent:
    """Correlates an incident with recent code and release activity."""

    @staticmethod
    async def analyze(
        incident,
        observability_result: ObservabilityResult,
    ) -> tuple[
        ReleaseAnalysisResult,
        list[EvidenceItem],
    ]:
        logger.info(
            "Release correlation started | incident_id=%s",
            incident.incident_id,
        )

        evidence: list[EvidenceItem] = []
        supporting_evidence: list[str] = []
        contradicting_evidence: list[str] = []
        changed_files: list[str] = []

        selected_commit: dict | None = None
        commit_sha: str | None = None
        pull_request: str | None = None
        previous_version: str | None = None

        recent_commits = await GitHubClient.get_recent_commits(
            lookback_hours=RELEASE_LOOKBACK_HOURS,
        )

        if recent_commits:
            selected_commit = recent_commits[0]
            commit_sha = selected_commit.get("sha")

            commit_details = selected_commit.get(
                "commit",
                {},
            )

            commit_message = commit_details.get(
                "message",
                "",
            )

            commit_author = commit_details.get(
                "author",
                {},
            )

            commit_date = commit_author.get("date")

            supporting_message = (
                "A repository commit exists within the "
                "configured release lookback period."
            )

            supporting_evidence.append(
                supporting_message
            )

            evidence.append(
                EvidenceItem(
                    source="GITHUB",
                    evidence_type="RECENT_COMMIT",
                    reference=commit_sha,
                    summary=(
                        "Recent repository commit found: "
                        f"{commit_message[:200]}"
                    ),
                    supports_hypothesis=True,
                    confidence=50.0,
                    raw_evidence={
                        "commit_sha": commit_sha,
                        "commit_message": commit_message,
                        "commit_date": commit_date,
                    },
                )
            )

            if commit_sha:
                full_commit_details = (
                    await GitHubClient.get_commit_details(
                        commit_sha=commit_sha,
                    )
                )

                changed_files = [
                    file_details.get("filename")
                    for file_details
                    in full_commit_details.get(
                        "files",
                        [],
                    )
                    if file_details.get("filename")
                ]

                if changed_files:
                    supporting_evidence.append(
                        (
                            "The recent commit changed "
                            f"{len(changed_files)} file(s)."
                        )
                    )

                    evidence.append(
                        EvidenceItem(
                            source="GITHUB",
                            evidence_type="CHANGED_FILES",
                            reference=commit_sha,
                            summary=(
                                "Files were changed in the "
                                "recent repository commit."
                            ),
                            supports_hypothesis=True,
                            confidence=55.0,
                            raw_evidence={
                                "changed_files":
                                    changed_files,
                            },
                        )
                    )

        else:
            contradicting_message = (
                "No recent repository commits were "
                "available within the configured "
                "release lookback period."
            )

            contradicting_evidence.append(
                contradicting_message
            )

            evidence.append(
                EvidenceItem(
                    source="GITHUB",
                    evidence_type="NO_RECENT_COMMIT",
                    reference=None,
                    summary=contradicting_message,
                    supports_hypothesis=False,
                    confidence=60.0,
                    raw_evidence={
                        "release_lookback_hours":
                            RELEASE_LOOKBACK_HOURS,
                    },
                )
            )

        current_version = (
            incident.deployed_version
            or observability_result.current_version
        )

        if current_version:
            supporting_message = (
                "The incident payload identifies "
                f"deployed version {current_version}."
            )

            supporting_evidence.append(
                supporting_message
            )

            evidence.append(
                EvidenceItem(
                    source="DATADOG",
                    evidence_type="DEPLOYED_VERSION",
                    reference=incident.source_event_id,
                    summary=supporting_message,
                    supports_hypothesis=True,
                    confidence=60.0,
                    raw_evidence={
                        "current_version":
                            current_version,
                    },
                )
            )

        else:
            contradicting_message = (
                "No deployed version was provided in "
                "the Datadog incident payload."
            )

            contradicting_evidence.append(
                contradicting_message
            )

            evidence.append(
                EvidenceItem(
                    source="DATADOG",
                    evidence_type="MISSING_VERSION",
                    reference=incident.source_event_id,
                    summary=contradicting_message,
                    supports_hypothesis=False,
                    confidence=65.0,
                    raw_evidence={},
                )
            )

        if (
            changed_files
            and observability_result.affected_components
       ):
            normalized_components = [
                component.lower()
                for component
                in observability_result.affected_components
            ]

            matching_files = [
                filename
                for filename in changed_files
                if any(
                    component in filename.lower()
                    for component
                    in normalized_components
                )
            ]

            if matching_files:
                supporting_message = (
                    "Recent changes include files whose "
                    "names match an affected component."
                )

                supporting_evidence.append(
                    supporting_message
                )

                evidence.append(
                    EvidenceItem(
                        source="GITHUB",
                        evidence_type=(
                            "AFFECTED_COMPONENT_FILE_MATCH"
                        ),
                        reference=commit_sha,
                        summary=supporting_message,
                        supports_hypothesis=True,
                        confidence=75.0,
                        raw_evidence={
                            "matching_files":
                                matching_files,
                            "affected_components":
                                observability_result
                                .affected_components,
                        },
                    )
                )

        confidence = (
            EvidenceValidator.calculate_confidence(
                evidence
            )
        )

        release_related = confidence >= 60.0

        if release_related:
            conclusion = (
                "A relationship with recent code or "
                "release activity is likely. This is "
                "correlation evidence and requires human "
                "validation before declaring the release "
                "as the confirmed cause."
            )
        else:
            conclusion = (
                "The available evidence does not establish "
                "a reliable relationship with a recent "
                "code change or release."
            )

        logger.info(
            "Release correlation completed | "
            "incident_id=%s | "
            "release_related=%s | "
            "confidence=%s",
            incident.incident_id,
            release_related,
            confidence,
        )

        result = ReleaseAnalysisResult(
            release_related=release_related,
            confidence=confidence,
            current_version=current_version,
            previous_version=previous_version,
            commit_sha=commit_sha,
            pull_request=pull_request,
            changed_files=changed_files,
            supporting_evidence=supporting_evidence,
            contradicting_evidence=(
                contradicting_evidence
            ),
            conclusion=conclusion,
        )

        return result, evidence
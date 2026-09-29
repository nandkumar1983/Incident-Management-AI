from app.api.agent_schemas import (
    FixRecommendation,
    ObservabilityResult,
    RegressionAnalysisResult,
    ReleaseAnalysisResult,
)
from app.core.config import (
    ALLOW_AUTOMATIC_CODE_CHANGE,
)
from app.core.logger import logger


class CodeFixRecommendationAgent:

    @staticmethod
    async def recommend(
        incident,
        observability_result: ObservabilityResult,
        release_result: ReleaseAnalysisResult,
        regression_result: RegressionAnalysisResult,
    ) -> FixRecommendation:

        logger.info(
            "Code-fix recommendation started | "
            "incident_id=%s",
            incident.incident_id,
        )

        description = incident.description.lower()

        likely_file = None
        likely_function = None

        if release_result.changed_files:
            likely_file = release_result.changed_files[0]

        if "database" in description:
            component = "Database access layer"

            approach = (
                "Review connection creation, timeout handling, "
                "retry policy and connection-pool configuration. "
                "Ensure transient database errors are handled "
                "without creating retry storms."
            )

            sample_pseudocode = (
                "try:\n"
                "    result = repository.execute()\n"
                "except TransientDatabaseError:\n"
                "    retry_with_bounded_backoff()\n"
                "except PermanentDatabaseError:\n"
                "    fail_without_retry()"
            )

            tests = [
                "Successful database connection",
                "Database connection timeout",
                "Connection refused",
                "Transient failure followed by recovery",
                "Maximum retries reached",
                "Connection pool exhaustion",
            ]

            risks = [
                "Excessive retries could increase database load",
                "Long timeouts could increase customer latency",
            ]

        elif "null" in description or "none" in description:
            component = "Application validation layer"

            approach = (
                "Validate upstream responses before accessing "
                "required fields. Preserve the existing business "
                "decision path when mandatory data is absent."
            )

            sample_pseudocode = (
                "response = dependency.get_data()\n"
                "if response is None:\n"
                "    return controlled_failure()\n"
                "validate_required_fields(response)"
            )

            tests = [
                "Valid dependency response",
                "Null dependency response",
                "Response with missing mandatory field",
                "Malformed response",
                "Dependency timeout",
            ]

            risks = [
                "Incorrect fallback could hide a real outage",
                "Default values could alter business decisions",
            ]

        elif "timeout" in description:
            component = "External-service integration layer"

            approach = (
                "Review client timeout values, connection reuse, "
                "circuit-breaker behavior and bounded retries. "
                "Do not retry non-idempotent operations unless "
                "the business operation supports it."
            )

            sample_pseudocode = (
                "with timeout(configured_timeout):\n"
                "    response = dependency.call()\n"
                "if transient_failure:\n"
                "    bounded_retry()\n"
                "if repeated_failure:\n"
                "    open_circuit()"
            )

            tests = [
                "Dependency responds within timeout",
                "Dependency exceeds timeout",
                "Circuit breaker opens",
                "Circuit breaker recovers",
                "Non-idempotent request is not duplicated",
            ]

            risks = [
                "Retries may duplicate business operations",
                "Circuit breaker thresholds may be too aggressive",
            ]

        else:
            component = (
                incident.service_name
                or incident.application_name
            )

            approach = (
                "Reproduce the alert condition using the "
                "captured payload, identify the first failing "
                "function from the stack trace, compare that "
                "function with the previous deployed version, "
                "then add a focused defensive fix and regression "
                "test."
            )

            sample_pseudocode = None

            tests = [
                "Reproduction test using incident payload",
                "Positive functional test",
                "Negative functional test",
                "Boundary-value test",
                "Regression test for the incident signature",
            ]

            risks = [
                "Insufficient telemetry may point to the wrong layer",
                "A symptom-level fix may not remove the root cause",
            ]

        rollback_approach = (
            "If the release correlation is validated and the "
            "service breaches the approved rollback threshold, "
            "redeploy the previously validated version through "
            "the approved change process."
        )

        return FixRecommendation(
            component=component,
            likely_file=likely_file,
            likely_function=likely_function,
            approach=approach,
            sample_pseudocode=sample_pseudocode,
            tests_required=tests,
            rollback_approach=rollback_approach,
            risks=risks,
            production_change_allowed=(
                ALLOW_AUTOMATIC_CODE_CHANGE
            ),
        )
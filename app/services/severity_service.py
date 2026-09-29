class SeverityService:

    @staticmethod
    def predict(
        environment: str,
        description: str,
        application_name: str | None = None,
    ) -> str:

        normalized_environment = environment.strip().lower()
        normalized_description = description.strip().lower()
        normalized_application = (
            application_name or ""
        ).strip().lower()

        production_environment = (
            normalized_environment
            in {
                "production",
                "prod",
            }
        )

        payment_failure = (
            "payment" in normalized_description
            or "payment" in normalized_application
        ) and any(
            word in normalized_description
            for word in {
                "failed",
                "failure",
                "unavailable",
                "down",
                "declined",
            }
        )

        database_error = any(
            word in normalized_description
            for word in {
                "database",
                "db connection",
                "sql exception",
                "connection refused",
                "connection timeout",
            }
        )

        if production_environment and payment_failure:
            return "Critical"

        if production_environment and database_error:
            return "High"

        if normalized_environment == "uat":
            return "Medium"

        if normalized_environment in {
            "development",
            "dev",
        }:
            return "Low"

        return "Medium"
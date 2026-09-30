from typing import Any


class DemoPaymentService:
    """
    Development-only payment service used to demonstrate
    controlled incident generation.

    This service must never be enabled in production.
    """

    @staticmethod
    def get_customer_profile(
        customer_id: str,
        inject_fault: bool,
    ) -> dict[str, Any] | None:

        if inject_fault:
            return None

        return {
            "customer_id": customer_id,
            "status": "ACTIVE",
            "risk_level": "LOW",
        }

    @staticmethod
    def authorize_payment(
        customer_id: str,
        amount: float,
        inject_fault: bool,
    ) -> dict[str, Any]:

        profile = (
            DemoPaymentService.get_customer_profile(
                customer_id=customer_id,
                inject_fault=inject_fault,
            )
        )

        # Deliberate defect for the demonstration:
        # profile may be None, but the code accesses it
        # without validating the response.
        customer_status = profile["status"]

        if customer_status != "ACTIVE":
            return {
                "authorized": False,
                "reason": "Customer profile is not active",
            }

        return {
            "authorized": True,
            "customer_id": customer_id,
            "amount": amount,
        }
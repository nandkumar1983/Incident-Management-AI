from app.api.agent_schemas import EvidenceItem


class EvidenceValidator:

    @staticmethod
    def calculate_confidence(
        evidence: list[EvidenceItem],
    ) -> float:

        if not evidence:
            return 0.0

        supporting_scores = [
            item.confidence
            for item in evidence
            if item.supports_hypothesis
        ]

        contradicting_scores = [
            item.confidence
            for item in evidence
            if not item.supports_hypothesis
        ]

        if not supporting_scores:
            return 0.0

        supporting_average = (
            sum(supporting_scores)
            / len(supporting_scores)
        )

        contradiction_penalty = 0.0

        if contradicting_scores:
            contradiction_penalty = (
                sum(contradicting_scores)
                / len(contradicting_scores)
            ) * 0.35

        result = max(
            0.0,
            min(
                100.0,
                supporting_average
                - contradiction_penalty,
            ),
        )

        return round(
            result,
            2,
        )

    @staticmethod
    def confidence_label(
        confidence: float,
    ) -> str:

        if confidence >= 95:
            return "Confirmed"

        if confidence >= 80:
            return "Highly likely"

        if confidence >= 60:
            return "Likely"

        if confidence >= 40:
            return "Possible"

        return "Insufficient evidence"
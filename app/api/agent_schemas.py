from typing import Any, Literal

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    source: Literal[
        "DATADOG",
        "SERVICENOW",
        "GITHUB",
        "DATABASE",
        "CMDB",
        "AGENT",
    ]

    evidence_type: str
    reference: str | None = None
    summary: str
    supports_hypothesis: bool
    confidence: float = Field(ge=0, le=100)
    raw_evidence: dict[str, Any] = Field(
        default_factory=dict
    )


class ObservabilityResult(BaseModel):
    incident_id: str
    service: str | None
    current_version: str | None
    error_signatures: list[str]
    affected_components: list[str]
    findings: list[str]
    evidence: list[EvidenceItem]


class ReleaseAnalysisResult(BaseModel):
    release_related: bool
    confidence: float = Field(ge=0, le=100)
    current_version: str | None
    previous_version: str | None
    commit_sha: str | None
    pull_request: str | None
    changed_files: list[str]
    supporting_evidence: list[str]
    contradicting_evidence: list[str]
    conclusion: str


class RegressionAnalysisResult(BaseModel):
    regression_related: bool
    confidence: float = Field(ge=0, le=100)
    previous_incident_id: str | None
    previous_fix_reference: str | None
    similar_error_found: bool
    findings: list[str]


class FixRecommendation(BaseModel):
    component: str
    likely_file: str | None = None
    likely_function: str | None = None
    approach: str
    sample_pseudocode: str | None = None
    tests_required: list[str]
    rollback_approach: str
    risks: list[str]
    production_change_allowed: bool = False


class InvestigationResult(BaseModel):
    incident_id: str
    investigation_id: str | None = None

    investigation_status: Literal[
        "COMPLETED",
        "PARTIAL",
        "INSUFFICIENT_EVIDENCE",
    ]

    investigation_summary: str
    probable_root_cause: str | None
    affected_component: str | None

    release_analysis: ReleaseAnalysisResult
    regression_analysis: RegressionAnalysisResult
    fix_recommendation: FixRecommendation | None

    immediate_mitigation: list[str]
    evidence: list[EvidenceItem]

    human_approval_required: bool = True
    approval_status: str = "PENDING"
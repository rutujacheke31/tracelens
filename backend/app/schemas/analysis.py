from typing import Literal

from pydantic import BaseModel, Field


class EvidenceChunkAnalysis(BaseModel):
    """Important debugging evidence extracted from one document chunk."""

    relevant: bool = Field(
        description="Whether this chunk contains useful bug evidence."
    )

    error_messages: list[str] = Field(
        description="Exact or clearly identified errors found in the chunk."
    )

    technical_findings: list[str] = Field(
        description="Logs, stack traces, symptoms, or technical observations."
    )

    possible_causes: list[str] = Field(
        description="Possible causes suggested by this chunk."
    )


class BugAnalysisResult(BaseModel):
    """Final structured diagnosis returned by TraceLens."""

    summary: str = Field(
        description="Concise explanation of the reported problem."
    )

    severity: Literal[
        "low",
        "medium",
        "high",
        "critical",
        "unknown",
    ] = Field(
        description="Estimated impact of the bug."
    )

    detected_errors: list[str] = Field(
        description="Errors detected across all supplied evidence."
    )

    screenshot_observations: list[str] = Field(
        description="Relevant information visible in the screenshot."
    )

    supporting_file_findings: list[str] = Field(
        description="Relevant evidence found in the supporting file."
    )

    likely_root_causes: list[str] = Field(
        description="Most likely technical causes, ordered by likelihood."
    )

    evidence: list[str] = Field(
        description="Evidence supporting the proposed root causes."
    )

    recommended_fixes: list[str] = Field(
        description="Practical steps for fixing the bug."
    )

    verification_steps: list[str] = Field(
        description="Steps for verifying that the bug has been fixed."
    )

    confidence: Literal[
        "low",
        "medium",
        "high",
    ] = Field(
        description="Confidence in the diagnosis based on available evidence."
    )

    missing_information: list[str] = Field(
        description="Additional information required for a better diagnosis."
    )
"""Analysis result models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from xcresult_ai_assistant.models.failure import (
    FailureCategory,
    FailureSeverity,
    TestFailure,
)


class ConfidenceLevel(str, Enum):
    """Confidence level in analysis."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"


class DebugSuggestion(BaseModel):
    """Debugging suggestion for a failure."""

    title: str = Field(..., description="Short suggestion title")
    description: str = Field(..., description="Detailed explanation")
    action: str = Field(default="", description="Recommended action")
    code_example: str = Field(default="", description="Code example if applicable")
    priority: int = Field(default=1, ge=1, le=5, description="Priority 1-5")
    category: str = Field(default="general", description="Suggestion category")
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM)
    related_docs: list[str] = Field(default_factory=list, description="Related documentation links")
    tags: list[str] = Field(default_factory=list, description="Tags for filtering")

    @property
    def is_high_confidence(self) -> bool:
        """Check if suggestion has high confidence."""
        return self.confidence == ConfidenceLevel.HIGH


class RootCauseAnalysis(BaseModel):
    """Root cause analysis for a failure."""

    summary: str = Field(..., description="Brief root cause summary")
    detailed_explanation: str = Field(default="", description="Detailed explanation")
    category: FailureCategory = Field(..., description="Root cause category")
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM)
    evidence: list[str] = Field(default_factory=list, description="Supporting evidence")
    affected_components: list[str] = Field(default_factory=list, description="Affected code components")
    suggestions: list[DebugSuggestion] = Field(default_factory=list, description="Fix suggestions")
    similar_failures: list[str] = Field(default_factory=list, description="Similar failure names")
    is_flaky_indicator: bool = Field(default=False, description="Indicates flaky pattern")
    requires_investigation: bool = Field(default=False, description="Needs deeper investigation")

    @property
    def top_suggestion(self) -> DebugSuggestion | None:
        """Get highest priority suggestion."""
        if not self.suggestions:
            return None
        return sorted(self.suggestions, key=lambda s: s.priority)[0]


class AnalysisResult(BaseModel):
    """Complete analysis result for a test run."""

    source_path: str = Field(..., description="Source file/bundle analyzed")
    timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    total_tests: int = Field(default=0, description="Total tests analyzed")
    passed_tests: int = Field(default=0, description="Passed tests count")
    failed_tests: int = Field(default=0, description="Failed tests count")
    skipped_tests: int = Field(default=0, description="Skipped tests count")
    failures: list[TestFailure] = Field(default_factory=list, description="Analyzed failures")
    root_causes: list[RootCauseAnalysis] = Field(default_factory=list, description="Root cause analyses")
    category_summary: dict[str, int] = Field(default_factory=dict, description="Failures by category")
    severity_summary: dict[str, int] = Field(default_factory=dict, description="Failures by severity")
    flaky_count: int = Field(default=0, description="Likely flaky failures")
    infrastructure_count: int = Field(default=0, description="Infrastructure issues")
    app_bugs_count: int = Field(default=0, description="Likely app bugs")
    analysis_duration: float = Field(default=0.0, description="Analysis time in seconds")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate percentage."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate percentage."""
        if self.total_tests == 0:
            return 0.0
        return (self.failed_tests / self.total_tests) * 100

    @property
    def top_categories(self) -> list[tuple[str, int]]:
        """Get top failure categories sorted by count."""
        return sorted(self.category_summary.items(), key=lambda x: x[1], reverse=True)

    @property
    def critical_failures(self) -> list[TestFailure]:
        """Get critical severity failures."""
        return [f for f in self.failures if f.severity == FailureSeverity.CRITICAL]

    @property
    def actionable_failures(self) -> list[TestFailure]:
        """Get actionable failures (not infrastructure)."""
        return [f for f in self.failures if f.is_actionable]

    @property
    def prioritized_failures(self) -> list[TestFailure]:
        """Get failures sorted by priority score."""
        return sorted(self.failures, key=lambda f: f.priority_score, reverse=True)

    def get_suggestions_for_category(self, category: FailureCategory) -> list[DebugSuggestion]:
        """Get all suggestions for a specific category."""
        suggestions = []
        for rca in self.root_causes:
            if rca.category == category:
                suggestions.extend(rca.suggestions)
        return suggestions

    def has_category(self, category: FailureCategory) -> bool:
        """Check if any failures match a category."""
        return any(f.category == category for f in self.failures)

"""Report configuration and output models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from xcresult_ai_assistant.models.analysis import AnalysisResult


class ReportFormat(str, Enum):
    """Output format for reports."""

    CONSOLE = "console"
    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"


class ReportConfig(BaseModel):
    """Configuration for report generation."""

    format: ReportFormat = Field(default=ReportFormat.CONSOLE)
    output_path: str = Field(default="", description="Output file path")
    include_suggestions: bool = Field(default=True, description="Include debug suggestions")
    include_stack_traces: bool = Field(default=False, description="Include full stack traces")
    include_screenshots: bool = Field(default=False, description="Include screenshot links")
    max_failures: int = Field(default=50, description="Maximum failures to include")
    group_by_category: bool = Field(default=True, description="Group failures by category")
    show_flaky_indicators: bool = Field(default=True, description="Show flaky test indicators")
    verbose: bool = Field(default=False, description="Verbose output mode")
    show_pass_rate: bool = Field(default=True, description="Show pass rate statistics")
    show_timing: bool = Field(default=True, description="Show timing information")
    title: str = Field(default="Test Analysis Report", description="Report title")


class AnalysisReport(BaseModel):
    """Generated analysis report."""

    title: str = Field(default="Test Analysis Report")
    generated_at: datetime = Field(default_factory=datetime.now)
    format: ReportFormat = Field(default=ReportFormat.CONSOLE)
    analysis: AnalysisResult = Field(..., description="Analysis result")
    config: ReportConfig = Field(default_factory=ReportConfig)
    content: str = Field(default="", description="Rendered report content")
    sections: dict[str, str] = Field(default_factory=dict, description="Report sections")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def has_failures(self) -> bool:
        """Check if report contains failures."""
        return self.analysis.failed_tests > 0

    @property
    def summary_line(self) -> str:
        """Generate one-line summary."""
        a = self.analysis
        status = "✅" if a.failed_tests == 0 else "❌"
        return (
            f"{status} {a.passed_tests}/{a.total_tests} passed "
            f"({a.pass_rate:.1f}%), {a.failed_tests} failures"
        )

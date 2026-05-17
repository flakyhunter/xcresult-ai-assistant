"""Data models for xcresult analysis."""

from xcresult_ai_assistant.models.test_result import (
    TestResult,
    TestStatus,
    TestSuite,
    TestRun,
)
from xcresult_ai_assistant.models.failure import (
    FailureCategory,
    FailureSeverity,
    TestFailure,
    FailurePattern,
)
from xcresult_ai_assistant.models.analysis import (
    AnalysisResult,
    DebugSuggestion,
    RootCauseAnalysis,
    ConfidenceLevel,
)
from xcresult_ai_assistant.models.report import (
    ReportFormat,
    ReportConfig,
    AnalysisReport,
)

__all__ = [
    # Test results
    "TestResult",
    "TestStatus",
    "TestSuite",
    "TestRun",
    # Failures
    "FailureCategory",
    "FailureSeverity",
    "TestFailure",
    "FailurePattern",
    # Analysis
    "AnalysisResult",
    "DebugSuggestion",
    "RootCauseAnalysis",
    "ConfidenceLevel",
    # Reports
    "ReportFormat",
    "ReportConfig",
    "AnalysisReport",
]

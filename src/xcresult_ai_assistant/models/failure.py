"""Failure categorization models."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FailureCategory(str, Enum):
    """Categories of test failures."""

    # Element/UI issues
    MISSING_ELEMENT = "missing_element"
    ELEMENT_NOT_HITTABLE = "element_not_hittable"
    ELEMENT_NOT_VISIBLE = "element_not_visible"
    WRONG_ELEMENT_STATE = "wrong_element_state"

    # Timing issues
    TIMEOUT = "timeout"
    WAIT_TIMEOUT = "wait_timeout"
    ANIMATION_TIMEOUT = "animation_timeout"

    # Assertion failures
    ASSERTION_FAILURE = "assertion_failure"
    VALUE_MISMATCH = "value_mismatch"
    STATE_MISMATCH = "state_mismatch"

    # Accessibility
    ACCESSIBILITY_MISSING = "accessibility_missing"
    ACCESSIBILITY_CHANGED = "accessibility_changed"

    # Network/API
    NETWORK_ERROR = "network_error"
    API_TIMEOUT = "api_timeout"
    API_ERROR = "api_error"

    # Async/Race conditions
    RACE_CONDITION = "race_condition"
    ASYNC_FAILURE = "async_failure"
    ORDER_DEPENDENCY = "order_dependency"

    # Visual/Snapshot
    SNAPSHOT_MISMATCH = "snapshot_mismatch"
    SCREENSHOT_DIFF = "screenshot_diff"
    LAYOUT_SHIFT = "layout_shift"

    # System interference
    SYSTEM_ALERT = "system_alert"
    KEYBOARD_ISSUE = "keyboard_issue"
    PERMISSION_DIALOG = "permission_dialog"
    NOTIFICATION = "notification"

    # Infrastructure
    SIMULATOR_CRASH = "simulator_crash"
    APP_CRASH = "app_crash"
    MEMORY_ISSUE = "memory_issue"
    RESOURCE_EXHAUSTION = "resource_exhaustion"

    # Data issues
    DATA_DEPENDENCY = "data_dependency"
    MOCK_FAILURE = "mock_failure"
    FIXTURE_ISSUE = "fixture_issue"

    # Unknown
    UNKNOWN = "unknown"
    UNCLASSIFIED = "unclassified"


class FailureSeverity(str, Enum):
    """Severity levels for failures."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FailurePattern(BaseModel):
    """Pattern for matching failure types."""

    name: str = Field(..., description="Pattern name")
    category: FailureCategory = Field(..., description="Failure category")
    severity: FailureSeverity = Field(default=FailureSeverity.MEDIUM)
    keywords: list[str] = Field(default_factory=list, description="Keywords to match")
    regex_patterns: list[str] = Field(default_factory=list, description="Regex patterns")
    description: str = Field(default="", description="Pattern description")
    is_flaky: bool = Field(default=False, description="Typically flaky pattern")
    is_infrastructure: bool = Field(default=False, description="Infrastructure issue")
    is_test_issue: bool = Field(default=False, description="Test code issue")
    is_app_issue: bool = Field(default=False, description="Application bug")


class TestFailure(BaseModel):
    """Analyzed test failure with categorization."""

    test_name: str = Field(..., description="Test method name")
    test_class: str = Field(default="", description="Test class name")
    category: FailureCategory = Field(..., description="Failure category")
    severity: FailureSeverity = Field(default=FailureSeverity.MEDIUM)
    message: str = Field(default="", description="Failure message")
    stack_trace: str = Field(default="", description="Stack trace")
    file_path: str = Field(default="", description="File where failure occurred")
    line_number: int = Field(default=0, description="Line number")
    matched_patterns: list[str] = Field(default_factory=list, description="Patterns matched")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Classification confidence")
    is_flaky: bool = Field(default=False, description="Likely flaky test")
    is_infrastructure: bool = Field(default=False, description="Infrastructure issue")
    is_test_issue: bool = Field(default=False, description="Test code issue")
    is_app_issue: bool = Field(default=False, description="Application bug")
    related_elements: list[str] = Field(default_factory=list, description="Related UI elements")
    duration: float = Field(default=0.0, description="Test duration")
    retry_count: int = Field(default=0, description="Retry attempts")
    screenshots: list[str] = Field(default_factory=list, description="Screenshot paths")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional data")

    @property
    def full_name(self) -> str:
        """Fully qualified test name."""
        if self.test_class:
            return f"{self.test_class}.{self.test_name}"
        return self.test_name

    @property
    def location(self) -> str:
        """File location string."""
        if self.file_path and self.line_number:
            return f"{self.file_path}:{self.line_number}"
        return self.file_path or "unknown"

    @property
    def is_actionable(self) -> bool:
        """Check if failure is actionable vs infrastructure noise."""
        return not self.is_infrastructure and self.severity != FailureSeverity.INFO

    @property
    def priority_score(self) -> int:
        """Calculate priority score for triage ordering."""
        score = 0
        # Severity weight
        severity_weights = {
            FailureSeverity.CRITICAL: 100,
            FailureSeverity.HIGH: 75,
            FailureSeverity.MEDIUM: 50,
            FailureSeverity.LOW: 25,
            FailureSeverity.INFO: 10,
        }
        score += severity_weights.get(self.severity, 50)

        # App bugs are higher priority
        if self.is_app_issue:
            score += 30

        # Flaky tests are lower priority
        if self.is_flaky:
            score -= 20

        # Infrastructure issues are lower priority
        if self.is_infrastructure:
            score -= 40

        # High confidence increases priority
        score += int(self.confidence * 20)

        return max(0, score)

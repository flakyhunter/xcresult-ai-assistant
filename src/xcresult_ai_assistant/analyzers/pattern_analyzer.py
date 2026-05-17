"""Pattern-based failure analyzer."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from xcresult_ai_assistant.models.failure import (
    FailureCategory,
    FailurePattern,
    FailureSeverity,
)


@dataclass
class PatternMatch:
    """Result of a pattern match."""

    pattern: FailurePattern
    matched_text: str
    confidence: float = 1.0
    context: str = ""


class PatternAnalyzer:
    """Analyzer that matches failure messages against known patterns."""

    def __init__(self) -> None:
        """Initialize with default patterns."""
        self.patterns = self._build_default_patterns()

    def _build_default_patterns(self) -> list[FailurePattern]:
        """Build comprehensive list of failure patterns."""
        return [
            # Element/UI Issues
            FailurePattern(
                name="missing_element",
                category=FailureCategory.MISSING_ELEMENT,
                severity=FailureSeverity.HIGH,
                keywords=["no matches found", "element not found", "unable to find", "doesn't exist"],
                regex_patterns=[
                    r"No matches found for",
                    r"Failed to find",
                    r"Element .* does not exist",
                    r"cannot find .* element",
                    r"XCUIElement.*not found",
                ],
                description="UI element could not be located",
                is_flaky=False,
                is_test_issue=True,
            ),
            FailurePattern(
                name="element_not_hittable",
                category=FailureCategory.ELEMENT_NOT_HITTABLE,
                severity=FailureSeverity.MEDIUM,
                keywords=["not hittable", "is not hittable", "cannot be tapped"],
                regex_patterns=[
                    r"Element .* is not hittable",
                    r"failed to tap .* not hittable",
                    r"isHittable.*false",
                ],
                description="Element exists but cannot be interacted with",
                is_flaky=True,
                is_test_issue=True,
            ),
            FailurePattern(
                name="element_not_visible",
                category=FailureCategory.ELEMENT_NOT_VISIBLE,
                severity=FailureSeverity.MEDIUM,
                keywords=["not visible", "is not visible", "visibility"],
                regex_patterns=[
                    r"Element .* is not visible",
                    r"isVisible.*false",
                    r"waitForExistence.*failed",
                ],
                description="Element exists but is not visible on screen",
                is_flaky=True,
            ),

            # Timeout Issues
            FailurePattern(
                name="wait_timeout",
                category=FailureCategory.WAIT_TIMEOUT,
                severity=FailureSeverity.MEDIUM,
                keywords=["timed out", "timeout", "exceeded time limit", "wait expired"],
                regex_patterns=[
                    r"Timed out waiting",
                    r"waitForExistence.*timed out",
                    r"exceeded.*timeout",
                    r"deadline exceeded",
                    r"wait.*expired",
                ],
                description="Wait operation timed out",
                is_flaky=True,
                is_test_issue=True,
            ),
            FailurePattern(
                name="animation_timeout",
                category=FailureCategory.ANIMATION_TIMEOUT,
                severity=FailureSeverity.LOW,
                keywords=["animation", "animating", "transition"],
                regex_patterns=[
                    r"animation.*timeout",
                    r"waiting for.*animation",
                    r"transition.*not complete",
                ],
                description="Animation did not complete in expected time",
                is_flaky=True,
                is_infrastructure=True,
            ),

            # Assertion Failures
            FailurePattern(
                name="assertion_failure",
                category=FailureCategory.ASSERTION_FAILURE,
                severity=FailureSeverity.HIGH,
                keywords=["xctassert", "assertion failed", "expected", "actual"],
                regex_patterns=[
                    r"XCTAssert.*failed",
                    r"assertion failed",
                    r"Expected .* but got",
                    r"#expect.*failed",
                ],
                description="Test assertion failed",
                is_app_issue=True,
            ),
            FailurePattern(
                name="value_mismatch",
                category=FailureCategory.VALUE_MISMATCH,
                severity=FailureSeverity.HIGH,
                keywords=["expected", "actual", "mismatch", "not equal"],
                regex_patterns=[
                    r"expected.*actual",
                    r"XCTAssertEqual.*failed",
                    r"values are not equal",
                    r"#expect\(.* == .*\).*failed",
                ],
                description="Expected value did not match actual value",
                is_app_issue=True,
            ),

            # Accessibility Issues
            FailurePattern(
                name="accessibility_missing",
                category=FailureCategory.ACCESSIBILITY_MISSING,
                severity=FailureSeverity.MEDIUM,
                keywords=["accessibility", "identifier", "accessibilityIdentifier"],
                regex_patterns=[
                    r"accessibilityIdentifier.*nil",
                    r"No accessibility identifier",
                    r"missing.*identifier",
                ],
                description="Accessibility identifier is missing",
                is_test_issue=True,
            ),

            # Network Issues
            FailurePattern(
                name="network_error",
                category=FailureCategory.NETWORK_ERROR,
                severity=FailureSeverity.MEDIUM,
                keywords=["network", "connection", "unreachable", "offline"],
                regex_patterns=[
                    r"network.*error",
                    r"connection.*failed",
                    r"host.*unreachable",
                    r"NSURLError",
                    r"no internet",
                ],
                description="Network connectivity issue",
                is_flaky=True,
                is_infrastructure=True,
            ),
            FailurePattern(
                name="api_timeout",
                category=FailureCategory.API_TIMEOUT,
                severity=FailureSeverity.MEDIUM,
                keywords=["api timeout", "request timeout", "server timeout"],
                regex_patterns=[
                    r"api.*timeout",
                    r"request.*timed out",
                    r"server.*not responding",
                    r"HTTP.*timeout",
                ],
                description="API request timed out",
                is_flaky=True,
                is_infrastructure=True,
            ),
            FailurePattern(
                name="api_error",
                category=FailureCategory.API_ERROR,
                severity=FailureSeverity.HIGH,
                keywords=["api error", "500", "server error", "bad request"],
                regex_patterns=[
                    r"HTTP.*[45]\d\d",
                    r"server error",
                    r"bad request",
                    r"API.*failed",
                ],
                description="API returned an error",
                is_app_issue=True,
            ),

            # Async/Race Conditions
            FailurePattern(
                name="race_condition",
                category=FailureCategory.RACE_CONDITION,
                severity=FailureSeverity.MEDIUM,
                keywords=["race condition", "concurrent", "threading"],
                regex_patterns=[
                    r"race condition",
                    r"concurrent.*access",
                    r"thread.*safety",
                    r"data race",
                ],
                description="Possible race condition detected",
                is_flaky=True,
                is_app_issue=True,
            ),
            FailurePattern(
                name="async_failure",
                category=FailureCategory.ASYNC_FAILURE,
                severity=FailureSeverity.MEDIUM,
                keywords=["async", "await", "completion", "callback"],
                regex_patterns=[
                    r"async.*failed",
                    r"completion.*not called",
                    r"callback.*timeout",
                    r"expectation.*fulfilled",
                ],
                description="Async operation did not complete as expected",
                is_flaky=True,
            ),

            # Snapshot/Visual Issues
            FailurePattern(
                name="snapshot_mismatch",
                category=FailureCategory.SNAPSHOT_MISMATCH,
                severity=FailureSeverity.MEDIUM,
                keywords=["snapshot", "reference image", "pixel difference"],
                regex_patterns=[
                    r"snapshot.*mismatch",
                    r"reference image.*differ",
                    r"pixel.*difference",
                    r"visual.*regression",
                ],
                description="Visual snapshot does not match reference",
                is_app_issue=True,
            ),
            FailurePattern(
                name="screenshot_diff",
                category=FailureCategory.SCREENSHOT_DIFF,
                severity=FailureSeverity.LOW,
                keywords=["screenshot", "image comparison", "visual diff"],
                regex_patterns=[
                    r"screenshot.*differ",
                    r"image.*mismatch",
                ],
                description="Screenshot comparison failed",
                is_flaky=True,
            ),

            # System Interference
            FailurePattern(
                name="system_alert",
                category=FailureCategory.SYSTEM_ALERT,
                severity=FailureSeverity.LOW,
                keywords=["system alert", "permission dialog", "springboard"],
                regex_patterns=[
                    r"system.*alert",
                    r"permission.*dialog",
                    r"springboard.*interrupt",
                    r"unexpected.*alert",
                ],
                description="System alert interfered with test",
                is_flaky=True,
                is_infrastructure=True,
            ),
            FailurePattern(
                name="keyboard_issue",
                category=FailureCategory.KEYBOARD_ISSUE,
                severity=FailureSeverity.LOW,
                keywords=["keyboard", "keyboard dismiss", "type text"],
                regex_patterns=[
                    r"keyboard.*not.*dismiss",
                    r"typeText.*failed",
                    r"keyboard.*blocking",
                ],
                description="Keyboard-related interaction issue",
                is_flaky=True,
                is_test_issue=True,
            ),
            FailurePattern(
                name="notification",
                category=FailureCategory.NOTIFICATION,
                severity=FailureSeverity.LOW,
                keywords=["notification", "banner", "push notification"],
                regex_patterns=[
                    r"notification.*interfere",
                    r"banner.*blocking",
                ],
                description="Notification interfered with test",
                is_flaky=True,
                is_infrastructure=True,
            ),

            # Infrastructure Issues
            FailurePattern(
                name="simulator_crash",
                category=FailureCategory.SIMULATOR_CRASH,
                severity=FailureSeverity.CRITICAL,
                keywords=["simulator crash", "simctl", "boot failed"],
                regex_patterns=[
                    r"simulator.*crash",
                    r"simctl.*error",
                    r"boot.*failed",
                    r"CoreSimulator",
                ],
                description="iOS Simulator crashed or failed to boot",
                is_infrastructure=True,
            ),
            FailurePattern(
                name="app_crash",
                category=FailureCategory.APP_CRASH,
                severity=FailureSeverity.CRITICAL,
                keywords=["crash", "exc_bad_access", "sigabrt", "fatal error"],
                regex_patterns=[
                    r"CRASH",
                    r"EXC_BAD_ACCESS",
                    r"SIGABRT",
                    r"SIGSEGV",
                    r"Fatal error",
                    r"fatalError",
                    r"crashed",
                ],
                description="Application crashed during test",
                is_app_issue=True,
            ),
            FailurePattern(
                name="memory_issue",
                category=FailureCategory.MEMORY_ISSUE,
                severity=FailureSeverity.HIGH,
                keywords=["memory", "out of memory", "memory warning"],
                regex_patterns=[
                    r"out of memory",
                    r"memory warning",
                    r"memory pressure",
                    r"malloc.*failed",
                ],
                description="Memory-related issue",
                is_app_issue=True,
            ),

            # Data Issues
            FailurePattern(
                name="data_dependency",
                category=FailureCategory.DATA_DEPENDENCY,
                severity=FailureSeverity.MEDIUM,
                keywords=["data", "fixture", "test data", "precondition"],
                regex_patterns=[
                    r"data.*not found",
                    r"fixture.*missing",
                    r"precondition.*failed",
                    r"setup.*failed",
                ],
                description="Test data dependency issue",
                is_test_issue=True,
            ),
            FailurePattern(
                name="mock_failure",
                category=FailureCategory.MOCK_FAILURE,
                severity=FailureSeverity.MEDIUM,
                keywords=["mock", "stub", "fake", "spy"],
                regex_patterns=[
                    r"mock.*failed",
                    r"stub.*not called",
                    r"unexpected.*invocation",
                ],
                description="Mock or stub configuration issue",
                is_test_issue=True,
            ),
        ]

    def analyze(self, text: str) -> list[PatternMatch]:
        """Analyze text and return all matching patterns."""
        matches: list[PatternMatch] = []
        text_lower = text.lower()

        for pattern in self.patterns:
            match = self._check_pattern(pattern, text, text_lower)
            if match:
                matches.append(match)

        # Sort by confidence (descending)
        matches.sort(key=lambda m: m.confidence, reverse=True)
        return matches

    def _check_pattern(
        self,
        pattern: FailurePattern,
        text: str,
        text_lower: str,
    ) -> PatternMatch | None:
        """Check if a pattern matches the text."""
        matched_text = ""
        confidence = 0.0

        # Check keywords
        for keyword in pattern.keywords:
            if keyword.lower() in text_lower:
                matched_text = keyword
                confidence = max(confidence, 0.7)

        # Check regex patterns (higher confidence)
        for regex_str in pattern.regex_patterns:
            try:
                regex = re.compile(regex_str, re.IGNORECASE)
                match = regex.search(text)
                if match:
                    matched_text = match.group(0)
                    confidence = max(confidence, 0.9)
            except re.error:
                continue

        if confidence > 0:
            return PatternMatch(
                pattern=pattern,
                matched_text=matched_text,
                confidence=confidence,
            )

        return None

    def get_patterns_by_category(
        self,
        category: FailureCategory,
    ) -> list[FailurePattern]:
        """Get all patterns for a specific category."""
        return [p for p in self.patterns if p.category == category]

    def get_flaky_patterns(self) -> list[FailurePattern]:
        """Get patterns that indicate flaky tests."""
        return [p for p in self.patterns if p.is_flaky]

    def get_infrastructure_patterns(self) -> list[FailurePattern]:
        """Get patterns for infrastructure issues."""
        return [p for p in self.patterns if p.is_infrastructure]

"""Detector for flaky test patterns."""

from __future__ import annotations

from dataclasses import dataclass, field

from xcresult_ai_assistant.models.failure import FailureCategory, TestFailure


@dataclass
class FlakyIndicator:
    """Indicator of flaky test behavior."""

    name: str
    description: str
    confidence: float = 0.5
    suggestions: list[str] = field(default_factory=list)


class FlakyDetector:
    """Detector for identifying flaky test patterns."""

    # Categories that are typically flaky
    FLAKY_CATEGORIES = {
        FailureCategory.TIMEOUT,
        FailureCategory.WAIT_TIMEOUT,
        FailureCategory.ANIMATION_TIMEOUT,
        FailureCategory.ELEMENT_NOT_HITTABLE,
        FailureCategory.ELEMENT_NOT_VISIBLE,
        FailureCategory.RACE_CONDITION,
        FailureCategory.ASYNC_FAILURE,
        FailureCategory.SYSTEM_ALERT,
        FailureCategory.KEYBOARD_ISSUE,
        FailureCategory.NOTIFICATION,
        FailureCategory.NETWORK_ERROR,
        FailureCategory.SCREENSHOT_DIFF,
    }

    # Keywords that suggest flakiness
    FLAKY_KEYWORDS = [
        "intermittent",
        "sometimes",
        "occasionally",
        "random",
        "flaky",
        "unstable",
        "timing",
        "race",
        "animation",
        "not hittable",
        "wait",
        "timeout",
    ]

    def __init__(self) -> None:
        """Initialize detector."""
        self.indicators = self._build_indicators()

    def _build_indicators(self) -> list[FlakyIndicator]:
        """Build list of flaky indicators."""
        return [
            FlakyIndicator(
                name="timing_sensitivity",
                description="Test appears sensitive to timing/animation",
                confidence=0.7,
                suggestions=[
                    "Add explicit waits for animations to complete",
                    "Use waitForExistence() with appropriate timeouts",
                    "Consider disabling animations in test environment",
                ],
            ),
            FlakyIndicator(
                name="element_visibility",
                description="Test fails on element visibility intermittently",
                confidence=0.6,
                suggestions=[
                    "Verify element is fully loaded before interaction",
                    "Check for overlapping UI elements",
                    "Ensure proper view hierarchy setup",
                ],
            ),
            FlakyIndicator(
                name="network_dependency",
                description="Test depends on network timing",
                confidence=0.8,
                suggestions=[
                    "Mock network responses for deterministic testing",
                    "Add proper loading state handling",
                    "Increase network timeout values",
                ],
            ),
            FlakyIndicator(
                name="system_interference",
                description="System dialogs or notifications may interfere",
                confidence=0.5,
                suggestions=[
                    "Handle system alerts in test setup",
                    "Use addUIInterruptionMonitor",
                    "Disable notifications in test environment",
                ],
            ),
            FlakyIndicator(
                name="order_dependency",
                description="Test may depend on execution order",
                confidence=0.6,
                suggestions=[
                    "Ensure proper test isolation",
                    "Reset state in setUp/tearDown",
                    "Avoid shared state between tests",
                ],
            ),
            FlakyIndicator(
                name="async_race",
                description="Async operations may complete in different order",
                confidence=0.7,
                suggestions=[
                    "Use XCTestExpectation for async operations",
                    "Add proper synchronization points",
                    "Consider using actor-based synchronization",
                ],
            ),
        ]

    def detect(self, failures: list[TestFailure]) -> list[FlakyIndicator]:
        """Detect flaky patterns in failures."""
        detected: list[FlakyIndicator] = []

        for failure in failures:
            indicators = self._analyze_failure(failure)
            for indicator in indicators:
                if indicator not in detected:
                    detected.append(indicator)

        return detected

    def _analyze_failure(self, failure: TestFailure) -> list[FlakyIndicator]:
        """Analyze a single failure for flaky patterns."""
        indicators: list[FlakyIndicator] = []

        # Check category
        if failure.category in self.FLAKY_CATEGORIES:
            indicators.append(self._get_indicator_for_category(failure.category))

        # Check for flaky keywords in message
        message_lower = failure.message.lower()
        for keyword in self.FLAKY_KEYWORDS:
            if keyword in message_lower:
                indicators.append(FlakyIndicator(
                    name=f"keyword_{keyword}",
                    description=f"Contains flaky keyword: {keyword}",
                    confidence=0.5,
                ))
                break

        # Check if marked as flaky by analyzer
        if failure.is_flaky:
            indicators.append(FlakyIndicator(
                name="analyzer_flagged",
                description="Pattern analyzer flagged as potentially flaky",
                confidence=0.6,
            ))

        return indicators

    def _get_indicator_for_category(
        self,
        category: FailureCategory,
    ) -> FlakyIndicator:
        """Get indicator for a specific category."""
        category_indicators = {
            FailureCategory.TIMEOUT: self.indicators[0],  # timing_sensitivity
            FailureCategory.WAIT_TIMEOUT: self.indicators[0],
            FailureCategory.ANIMATION_TIMEOUT: self.indicators[0],
            FailureCategory.ELEMENT_NOT_HITTABLE: self.indicators[1],  # element_visibility
            FailureCategory.ELEMENT_NOT_VISIBLE: self.indicators[1],
            FailureCategory.NETWORK_ERROR: self.indicators[2],  # network_dependency
            FailureCategory.SYSTEM_ALERT: self.indicators[3],  # system_interference
            FailureCategory.KEYBOARD_ISSUE: self.indicators[3],
            FailureCategory.NOTIFICATION: self.indicators[3],
            FailureCategory.RACE_CONDITION: self.indicators[5],  # async_race
            FailureCategory.ASYNC_FAILURE: self.indicators[5],
        }
        return category_indicators.get(
            category,
            FlakyIndicator(
                name="unknown_flaky",
                description="Potentially flaky failure",
                confidence=0.4,
            ),
        )

    def calculate_flaky_score(self, failure: TestFailure) -> float:
        """Calculate a flakiness score from 0.0 to 1.0."""
        score = 0.0

        # Category contribution
        if failure.category in self.FLAKY_CATEGORIES:
            score += 0.3

        # Explicit flag
        if failure.is_flaky:
            score += 0.2

        # Infrastructure issues are often flaky
        if failure.is_infrastructure:
            score += 0.2

        # Retry count suggests flakiness
        if failure.retry_count > 0:
            score += min(0.3, failure.retry_count * 0.1)

        # Low confidence suggests unclear failure (possibly flaky)
        if failure.confidence < 0.5:
            score += 0.1

        return min(1.0, score)

    def get_flaky_summary(
        self,
        failures: list[TestFailure],
    ) -> dict[str, int | float | list[str]]:
        """Get summary of flaky patterns."""
        flaky_failures = [f for f in failures if self.calculate_flaky_score(f) > 0.5]
        indicators = self.detect(failures)

        return {
            "total_failures": len(failures),
            "likely_flaky": len(flaky_failures),
            "flaky_percentage": (
                len(flaky_failures) / len(failures) * 100 if failures else 0
            ),
            "indicators": [i.name for i in indicators],
            "recommendations": list(set(
                suggestion
                for indicator in indicators
                for suggestion in indicator.suggestions
            ))[:5],
        }

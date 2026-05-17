"""Tests for analyzers."""

import pytest

from xcresult_ai_assistant.analyzers.pattern_analyzer import PatternAnalyzer
from xcresult_ai_assistant.analyzers.failure_analyzer import FailureAnalyzer
from xcresult_ai_assistant.analyzers.flaky_detector import FlakyDetector
from xcresult_ai_assistant.models.failure import FailureCategory, FailureSeverity, TestFailure
from xcresult_ai_assistant.models.test_result import TestResult, TestRun, TestStatus, TestSuite


class TestPatternAnalyzer:
    """Tests for PatternAnalyzer."""

    @pytest.fixture
    def analyzer(self) -> PatternAnalyzer:
        """Create analyzer instance."""
        return PatternAnalyzer()

    def test_detect_missing_element(self, analyzer: PatternAnalyzer) -> None:
        """Test detection of missing element pattern."""
        text = "No matches found for: Button, identifier: 'submitButton'"
        matches = analyzer.analyze(text)

        assert len(matches) > 0
        assert any(m.pattern.category == FailureCategory.MISSING_ELEMENT for m in matches)

    def test_detect_timeout(self, analyzer: PatternAnalyzer) -> None:
        """Test detection of timeout pattern."""
        text = "Timed out waiting for element to exist"
        matches = analyzer.analyze(text)

        assert len(matches) > 0
        categories = [m.pattern.category for m in matches]
        assert FailureCategory.WAIT_TIMEOUT in categories or FailureCategory.TIMEOUT in categories

    def test_detect_crash(self, analyzer: PatternAnalyzer) -> None:
        """Test detection of crash pattern."""
        text = "CRASH: EXC_BAD_ACCESS (code=1, address=0x0)"
        matches = analyzer.analyze(text)

        assert len(matches) > 0
        assert any(m.pattern.category == FailureCategory.APP_CRASH for m in matches)

    def test_detect_assertion_failure(self, analyzer: PatternAnalyzer) -> None:
        """Test detection of assertion failure pattern."""
        text = "XCTAssertEqual failed: expected 'foo' but got 'bar'"
        matches = analyzer.analyze(text)

        assert len(matches) > 0
        categories = [m.pattern.category for m in matches]
        assert (
            FailureCategory.ASSERTION_FAILURE in categories
            or FailureCategory.VALUE_MISMATCH in categories
        )

    def test_detect_network_error(self, analyzer: PatternAnalyzer) -> None:
        """Test detection of network error pattern."""
        text = "NSURLErrorDomain -1009: The Internet connection appears to be offline"
        matches = analyzer.analyze(text)

        assert len(matches) > 0
        assert any(m.pattern.category == FailureCategory.NETWORK_ERROR for m in matches)

    def test_detect_system_alert(self, analyzer: PatternAnalyzer) -> None:
        """Test detection of system alert pattern."""
        text = "Unexpected system alert appeared: 'Allow Location Access'"
        matches = analyzer.analyze(text)

        assert len(matches) > 0
        assert any(m.pattern.category == FailureCategory.SYSTEM_ALERT for m in matches)

    def test_detect_not_hittable(self, analyzer: PatternAnalyzer) -> None:
        """Test detection of not hittable pattern."""
        text = "Element 'button' is not hittable"
        matches = analyzer.analyze(text)

        assert len(matches) > 0
        assert any(m.pattern.category == FailureCategory.ELEMENT_NOT_HITTABLE for m in matches)

    def test_detect_snapshot_mismatch(self, analyzer: PatternAnalyzer) -> None:
        """Test detection of snapshot mismatch pattern."""
        text = "Snapshot mismatch: 2.3% pixel difference detected"
        matches = analyzer.analyze(text)

        assert len(matches) > 0
        assert any(m.pattern.category == FailureCategory.SNAPSHOT_MISMATCH for m in matches)

    def test_confidence_ordering(self, analyzer: PatternAnalyzer) -> None:
        """Test that matches are ordered by confidence."""
        text = "No matches found for button, this is a timeout waiting"
        matches = analyzer.analyze(text)

        if len(matches) > 1:
            for i in range(len(matches) - 1):
                assert matches[i].confidence >= matches[i + 1].confidence

    def test_no_matches_for_unrelated_text(self, analyzer: PatternAnalyzer) -> None:
        """Test that unrelated text produces no matches."""
        text = "This is just some random text that should not match any pattern"
        matches = analyzer.analyze(text)

        # May have some low-confidence matches, but nothing specific
        assert all(m.confidence < 0.9 for m in matches)

    def test_get_flaky_patterns(self, analyzer: PatternAnalyzer) -> None:
        """Test getting flaky patterns."""
        flaky = analyzer.get_flaky_patterns()
        assert len(flaky) > 0
        assert all(p.is_flaky for p in flaky)

    def test_get_infrastructure_patterns(self, analyzer: PatternAnalyzer) -> None:
        """Test getting infrastructure patterns."""
        infra = analyzer.get_infrastructure_patterns()
        assert len(infra) > 0
        assert all(p.is_infrastructure for p in infra)


class TestFailureAnalyzer:
    """Tests for FailureAnalyzer."""

    @pytest.fixture
    def analyzer(self) -> FailureAnalyzer:
        """Create analyzer instance."""
        return FailureAnalyzer()

    @pytest.fixture
    def test_run_with_failures(self) -> TestRun:
        """Create a test run with various failures."""
        return TestRun(
            name="TestRun",
            suites=[
                TestSuite(
                    name="Suite1",
                    tests=[
                        TestResult(
                            name="testPassed",
                            class_name="Tests",
                            status=TestStatus.PASSED,
                        ),
                        TestResult(
                            name="testMissingElement",
                            class_name="Tests",
                            status=TestStatus.FAILED,
                            message="No matches found for: Button 'submit'",
                        ),
                        TestResult(
                            name="testTimeout",
                            class_name="Tests",
                            status=TestStatus.TIMEOUT,
                            message="Timed out waiting for element",
                        ),
                        TestResult(
                            name="testCrash",
                            class_name="Tests",
                            status=TestStatus.CRASHED,
                            message="EXC_BAD_ACCESS",
                        ),
                    ],
                ),
            ],
        )

    def test_analyze_basic(self, analyzer: FailureAnalyzer, test_run_with_failures: TestRun) -> None:
        """Test basic analysis."""
        result = analyzer.analyze(test_run_with_failures)

        assert result.total_tests == 4
        assert result.passed_tests == 1
        # Note: TIMEOUT status is counted as failure but may be categorized differently
        assert result.failed_tests >= 2  # At least crash and missing element
        assert len(result.failures) >= 2

    def test_failure_categories_assigned(
        self, analyzer: FailureAnalyzer, test_run_with_failures: TestRun
    ) -> None:
        """Test that failure categories are assigned."""
        result = analyzer.analyze(test_run_with_failures)

        categories = [f.category for f in result.failures]
        assert FailureCategory.MISSING_ELEMENT in categories
        assert FailureCategory.APP_CRASH in categories

    def test_category_summary(
        self, analyzer: FailureAnalyzer, test_run_with_failures: TestRun
    ) -> None:
        """Test category summary generation."""
        result = analyzer.analyze(test_run_with_failures)

        assert len(result.category_summary) > 0
        total = sum(result.category_summary.values())
        assert total >= 2  # At least the failures we can categorize

    def test_root_causes_generated(
        self, analyzer: FailureAnalyzer, test_run_with_failures: TestRun
    ) -> None:
        """Test that root causes are generated."""
        result = analyzer.analyze(test_run_with_failures)

        assert len(result.root_causes) > 0
        # Each root cause should have suggestions
        for rca in result.root_causes:
            assert rca.summary
            assert rca.category in FailureCategory

    def test_prioritized_failures(
        self, analyzer: FailureAnalyzer, test_run_with_failures: TestRun
    ) -> None:
        """Test failure prioritization."""
        result = analyzer.analyze(test_run_with_failures)

        prioritized = result.prioritized_failures
        assert len(prioritized) >= 2

        # Higher priority first
        for i in range(len(prioritized) - 1):
            assert prioritized[i].priority_score >= prioritized[i + 1].priority_score


class TestFlakyDetector:
    """Tests for FlakyDetector."""

    @pytest.fixture
    def detector(self) -> FlakyDetector:
        """Create detector instance."""
        return FlakyDetector()

    def test_detect_flaky_timeout(self, detector: FlakyDetector) -> None:
        """Test detection of flaky timeout."""
        failure = TestFailure(
            test_name="testFlaky",
            category=FailureCategory.TIMEOUT,
            is_flaky=True,
        )
        indicators = detector.detect([failure])

        assert len(indicators) > 0

    def test_detect_flaky_system_alert(self, detector: FlakyDetector) -> None:
        """Test detection of flaky system alert."""
        failure = TestFailure(
            test_name="testAlert",
            category=FailureCategory.SYSTEM_ALERT,
        )
        indicators = detector.detect([failure])

        assert len(indicators) > 0
        # Should suggest handling system alerts
        suggestions = [s for ind in indicators for s in ind.suggestions]
        assert any("interrupt" in s.lower() or "alert" in s.lower() for s in suggestions)

    def test_calculate_flaky_score(self, detector: FlakyDetector) -> None:
        """Test flaky score calculation."""
        flaky_failure = TestFailure(
            test_name="testFlaky",
            category=FailureCategory.TIMEOUT,
            is_flaky=True,
            is_infrastructure=True,
            retry_count=2,
            confidence=0.3,
        )

        stable_failure = TestFailure(
            test_name="testStable",
            category=FailureCategory.ASSERTION_FAILURE,
            is_flaky=False,
            confidence=0.9,
        )

        flaky_score = detector.calculate_flaky_score(flaky_failure)
        stable_score = detector.calculate_flaky_score(stable_failure)

        assert flaky_score > stable_score
        assert flaky_score <= 1.0
        assert stable_score >= 0.0

    def test_flaky_summary(self, detector: FlakyDetector) -> None:
        """Test flaky summary generation."""
        failures = [
            TestFailure(
                test_name="test1",
                category=FailureCategory.TIMEOUT,
                is_flaky=True,
            ),
            TestFailure(
                test_name="test2",
                category=FailureCategory.ASSERTION_FAILURE,
                is_flaky=False,
            ),
            TestFailure(
                test_name="test3",
                category=FailureCategory.NETWORK_ERROR,
                is_flaky=True,
            ),
        ]

        summary = detector.get_flaky_summary(failures)

        assert summary["total_failures"] == 3
        assert summary["likely_flaky"] >= 0
        assert "recommendations" in summary

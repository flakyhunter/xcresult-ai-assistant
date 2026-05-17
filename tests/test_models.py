"""Tests for data models."""

import pytest
from datetime import datetime, timedelta

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


class TestTestResult:
    """Tests for TestResult model."""

    def test_basic_creation(self) -> None:
        """Test basic TestResult creation."""
        result = TestResult(
            name="testLogin",
            class_name="LoginTests",
            status=TestStatus.PASSED,
            duration=1.5,
        )
        assert result.name == "testLogin"
        assert result.class_name == "LoginTests"
        assert result.status == TestStatus.PASSED
        assert result.duration == 1.5

    def test_full_name(self) -> None:
        """Test full name generation."""
        result = TestResult(
            name="testMethod",
            class_name="TestClass",
            suite_name="TestSuite",
            status=TestStatus.PASSED,
        )
        assert result.full_name == "TestSuite.TestClass.testMethod"

    def test_is_failure(self) -> None:
        """Test is_failure property."""
        passed = TestResult(name="test", status=TestStatus.PASSED)
        failed = TestResult(name="test", status=TestStatus.FAILED)
        crashed = TestResult(name="test", status=TestStatus.CRASHED)

        assert not passed.is_failure
        assert failed.is_failure
        assert crashed.is_failure

    def test_location(self) -> None:
        """Test location property."""
        result = TestResult(
            name="test",
            status=TestStatus.FAILED,
            file_path="/path/to/file.swift",
            line_number=42,
        )
        assert result.location == "/path/to/file.swift:42"

        result_no_line = TestResult(
            name="test",
            status=TestStatus.FAILED,
            file_path="/path/to/file.swift",
        )
        assert result_no_line.location == "/path/to/file.swift"


class TestTestSuite:
    """Tests for TestSuite model."""

    def test_counts(self) -> None:
        """Test test count calculations."""
        suite = TestSuite(
            name="MySuite",
            tests=[
                TestResult(name="test1", status=TestStatus.PASSED),
                TestResult(name="test2", status=TestStatus.PASSED),
                TestResult(name="test3", status=TestStatus.FAILED),
                TestResult(name="test4", status=TestStatus.SKIPPED),
            ],
        )

        assert suite.total_count == 4
        assert suite.passed_count == 2
        assert suite.failed_count == 1
        assert suite.skipped_count == 1

    def test_pass_rate(self) -> None:
        """Test pass rate calculation."""
        suite = TestSuite(
            name="MySuite",
            tests=[
                TestResult(name="test1", status=TestStatus.PASSED),
                TestResult(name="test2", status=TestStatus.PASSED),
                TestResult(name="test3", status=TestStatus.PASSED),
                TestResult(name="test4", status=TestStatus.FAILED),
            ],
        )
        assert suite.pass_rate == 75.0

    def test_empty_suite_pass_rate(self) -> None:
        """Test pass rate with empty suite."""
        suite = TestSuite(name="Empty")
        assert suite.pass_rate == 0.0


class TestTestRun:
    """Tests for TestRun model."""

    def test_all_tests(self) -> None:
        """Test all_tests aggregation."""
        run = TestRun(
            name="Run",
            suites=[
                TestSuite(
                    name="Suite1",
                    tests=[
                        TestResult(name="test1", status=TestStatus.PASSED),
                        TestResult(name="test2", status=TestStatus.FAILED),
                    ],
                ),
                TestSuite(
                    name="Suite2",
                    tests=[
                        TestResult(name="test3", status=TestStatus.PASSED),
                    ],
                ),
            ],
        )

        assert len(run.all_tests) == 3
        assert run.total_count == 3
        assert run.passed_count == 2
        assert run.failed_count == 1

    def test_failed_tests(self) -> None:
        """Test failed_tests filter."""
        run = TestRun(
            suites=[
                TestSuite(
                    name="Suite",
                    tests=[
                        TestResult(name="test1", status=TestStatus.PASSED),
                        TestResult(name="test2", status=TestStatus.FAILED),
                        TestResult(name="test3", status=TestStatus.CRASHED),
                    ],
                ),
            ],
        )

        failed = run.failed_tests
        assert len(failed) == 2
        assert all(t.is_failure for t in failed)

    def test_duration(self) -> None:
        """Test duration calculation."""
        now = datetime.now()
        run = TestRun(
            start_time=now,
            end_time=now + timedelta(seconds=30),
        )
        assert run.duration == timedelta(seconds=30)


class TestTestFailure:
    """Tests for TestFailure model."""

    def test_priority_score(self) -> None:
        """Test priority score calculation."""
        critical_bug = TestFailure(
            test_name="test",
            category=FailureCategory.APP_CRASH,
            severity=FailureSeverity.CRITICAL,
            is_app_issue=True,
            confidence=0.9,
        )

        low_flaky = TestFailure(
            test_name="test",
            category=FailureCategory.TIMEOUT,
            severity=FailureSeverity.LOW,
            is_flaky=True,
            confidence=0.5,
        )

        assert critical_bug.priority_score > low_flaky.priority_score

    def test_is_actionable(self) -> None:
        """Test is_actionable property."""
        actionable = TestFailure(
            test_name="test",
            category=FailureCategory.ASSERTION_FAILURE,
            severity=FailureSeverity.HIGH,
            is_infrastructure=False,
        )

        not_actionable = TestFailure(
            test_name="test",
            category=FailureCategory.SIMULATOR_CRASH,
            severity=FailureSeverity.MEDIUM,
            is_infrastructure=True,
        )

        assert actionable.is_actionable
        assert not not_actionable.is_actionable


class TestDebugSuggestion:
    """Tests for DebugSuggestion model."""

    def test_high_confidence(self) -> None:
        """Test high confidence detection."""
        high = DebugSuggestion(
            title="Test",
            description="Description",
            confidence=ConfidenceLevel.HIGH,
        )
        low = DebugSuggestion(
            title="Test",
            description="Description",
            confidence=ConfidenceLevel.LOW,
        )

        assert high.is_high_confidence
        assert not low.is_high_confidence


class TestAnalysisResult:
    """Tests for AnalysisResult model."""

    def test_pass_rate(self) -> None:
        """Test pass rate calculation."""
        result = AnalysisResult(
            source_path="test.log",
            total_tests=100,
            passed_tests=90,
            failed_tests=10,
        )
        assert result.pass_rate == 90.0
        assert result.failure_rate == 10.0

    def test_top_categories(self) -> None:
        """Test top categories sorting."""
        result = AnalysisResult(
            source_path="test.log",
            category_summary={
                "timeout": 5,
                "missing_element": 10,
                "crash": 2,
            },
        )

        top = result.top_categories
        assert top[0] == ("missing_element", 10)
        assert top[1] == ("timeout", 5)
        assert top[2] == ("crash", 2)


class TestReportConfig:
    """Tests for ReportConfig model."""

    def test_defaults(self) -> None:
        """Test default values."""
        config = ReportConfig()
        assert config.format == ReportFormat.CONSOLE
        assert config.include_suggestions is True
        assert config.max_failures == 50

    def test_custom_values(self) -> None:
        """Test custom configuration."""
        config = ReportConfig(
            format=ReportFormat.MARKDOWN,
            max_failures=10,
            include_stack_traces=True,
        )
        assert config.format == ReportFormat.MARKDOWN
        assert config.max_failures == 10
        assert config.include_stack_traces is True

"""Main failure analyzer that categorizes test failures."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

from xcresult_ai_assistant.analyzers.pattern_analyzer import PatternAnalyzer
from xcresult_ai_assistant.models.analysis import AnalysisResult, ConfidenceLevel, RootCauseAnalysis
from xcresult_ai_assistant.models.failure import (
    FailureCategory,
    FailureSeverity,
    TestFailure,
)
from xcresult_ai_assistant.models.test_result import TestResult, TestRun, TestStatus


class FailureAnalyzer:
    """Analyzer that categorizes test failures and provides root cause analysis."""

    def __init__(self, verbose: bool = False):
        """Initialize analyzer."""
        self.verbose = verbose
        self.pattern_analyzer = PatternAnalyzer()

    def analyze(self, test_run: TestRun) -> AnalysisResult:
        """Analyze a complete test run."""
        start_time = datetime.now()
        failures: list[TestFailure] = []
        root_causes: list[RootCauseAnalysis] = []
        category_counter: Counter[str] = Counter()
        severity_counter: Counter[str] = Counter()

        # Analyze each failed test
        for test in test_run.failed_tests:
            failure = self._analyze_test(test)
            failures.append(failure)
            category_counter[failure.category.value] += 1
            severity_counter[failure.severity.value] += 1

        # Generate root cause analyses grouped by category
        root_causes = self._generate_root_causes(failures)

        # Calculate statistics
        flaky_count = sum(1 for f in failures if f.is_flaky)
        infrastructure_count = sum(1 for f in failures if f.is_infrastructure)
        app_bugs_count = sum(1 for f in failures if f.is_app_issue)

        analysis_duration = (datetime.now() - start_time).total_seconds()

        return AnalysisResult(
            source_path=test_run.source_path,
            timestamp=datetime.now(),
            total_tests=test_run.total_count,
            passed_tests=test_run.passed_count,
            failed_tests=test_run.failed_count,
            skipped_tests=sum(
                1 for s in test_run.suites
                for t in s.tests
                if t.status == TestStatus.SKIPPED
            ),
            failures=failures,
            root_causes=root_causes,
            category_summary=dict(category_counter),
            severity_summary=dict(severity_counter),
            flaky_count=flaky_count,
            infrastructure_count=infrastructure_count,
            app_bugs_count=app_bugs_count,
            analysis_duration=analysis_duration,
            metadata={
                "device": test_run.device,
                "os_version": test_run.os_version,
                "xcode_version": test_run.xcode_version,
            },
        )

    def _analyze_test(self, test: TestResult) -> TestFailure:
        """Analyze a single failed test."""
        # Combine message and stack trace for analysis
        analysis_text = f"{test.message}\n{test.stack_trace}\n{test.raw_output}"

        # Run pattern matching
        matches = self.pattern_analyzer.analyze(analysis_text)

        # Determine category and attributes
        if matches:
            best_match = matches[0]
            category = best_match.pattern.category
            severity = best_match.pattern.severity
            confidence = best_match.confidence
            is_flaky = best_match.pattern.is_flaky
            is_infrastructure = best_match.pattern.is_infrastructure
            is_test_issue = best_match.pattern.is_test_issue
            is_app_issue = best_match.pattern.is_app_issue
            matched_patterns = [m.pattern.name for m in matches[:3]]
        else:
            category = self._infer_category(test)
            severity = FailureSeverity.MEDIUM
            confidence = 0.3
            is_flaky = False
            is_infrastructure = False
            is_test_issue = False
            is_app_issue = False
            matched_patterns = []

        # Adjust based on test status
        if test.status == TestStatus.CRASHED:
            category = FailureCategory.APP_CRASH
            severity = FailureSeverity.CRITICAL
            is_app_issue = True
        elif test.status == TestStatus.TIMEOUT:
            category = FailureCategory.TIMEOUT
            is_flaky = True

        # Extract related elements from message
        related_elements = self._extract_elements(analysis_text)

        return TestFailure(
            test_name=test.name,
            test_class=test.class_name,
            category=category,
            severity=severity,
            message=test.message,
            stack_trace=test.stack_trace,
            file_path=test.file_path,
            line_number=test.line_number,
            matched_patterns=matched_patterns,
            confidence=confidence,
            is_flaky=is_flaky,
            is_infrastructure=is_infrastructure,
            is_test_issue=is_test_issue,
            is_app_issue=is_app_issue,
            related_elements=related_elements,
            duration=test.duration,
            retry_count=test.retry_count,
            screenshots=test.attachments,
        )

    def _infer_category(self, test: TestResult) -> FailureCategory:
        """Infer category when no pattern matches."""
        message_lower = test.message.lower()

        # Simple keyword-based inference
        if "assert" in message_lower:
            return FailureCategory.ASSERTION_FAILURE
        if "timeout" in message_lower:
            return FailureCategory.TIMEOUT
        if "not found" in message_lower or "no matches" in message_lower:
            return FailureCategory.MISSING_ELEMENT
        if "crash" in message_lower:
            return FailureCategory.APP_CRASH

        return FailureCategory.UNCLASSIFIED

    def _extract_elements(self, text: str) -> list[str]:
        """Extract UI element identifiers from text."""
        import re

        elements: list[str] = []

        # Look for accessibility identifiers
        identifier_pattern = re.compile(r'identifier:\s*["\']([^"\']+)["\']')
        elements.extend(identifier_pattern.findall(text))

        # Look for element type patterns
        element_pattern = re.compile(r'(button|label|textField|cell|image)\s*["\']([^"\']+)["\']')
        for match in element_pattern.finditer(text):
            elements.append(f"{match.group(1)}: {match.group(2)}")

        return list(set(elements))[:5]  # Dedupe and limit

    def _generate_root_causes(
        self,
        failures: list[TestFailure],
    ) -> list[RootCauseAnalysis]:
        """Generate root cause analyses grouped by category."""
        from xcresult_ai_assistant.ai.suggestion_engine import SuggestionEngine

        engine = SuggestionEngine()
        root_causes: list[RootCauseAnalysis] = []

        # Group failures by category
        by_category: dict[FailureCategory, list[TestFailure]] = {}
        for failure in failures:
            if failure.category not in by_category:
                by_category[failure.category] = []
            by_category[failure.category].append(failure)

        # Generate RCA for each category
        for category, category_failures in by_category.items():
            # Get suggestions for this category
            suggestions = engine.get_suggestions(category)

            # Determine confidence based on consistency
            if len(category_failures) > 3:
                confidence = ConfidenceLevel.HIGH
            elif len(category_failures) > 1:
                confidence = ConfidenceLevel.MEDIUM
            else:
                confidence = ConfidenceLevel.LOW

            # Build evidence
            evidence = []
            for f in category_failures[:3]:
                if f.message:
                    evidence.append(f"• {f.test_name}: {f.message[:100]}")

            # Check for flaky indicators
            is_flaky_indicator = any(f.is_flaky for f in category_failures)

            root_cause = RootCauseAnalysis(
                summary=self._get_category_summary(category),
                detailed_explanation=self._get_category_explanation(category),
                category=category,
                confidence=confidence,
                evidence=evidence,
                affected_components=[f.test_name for f in category_failures],
                suggestions=suggestions,
                similar_failures=[f.full_name for f in category_failures],
                is_flaky_indicator=is_flaky_indicator,
                requires_investigation=len(category_failures) > 5,
            )
            root_causes.append(root_cause)

        return root_causes

    def _get_category_summary(self, category: FailureCategory) -> str:
        """Get summary description for a category."""
        summaries = {
            FailureCategory.MISSING_ELEMENT: "UI elements could not be located",
            FailureCategory.ELEMENT_NOT_HITTABLE: "Elements exist but cannot be tapped",
            FailureCategory.TIMEOUT: "Operations timed out waiting for conditions",
            FailureCategory.WAIT_TIMEOUT: "Wait operations exceeded timeout",
            FailureCategory.ASSERTION_FAILURE: "Test assertions did not pass",
            FailureCategory.VALUE_MISMATCH: "Expected values did not match actual values",
            FailureCategory.NETWORK_ERROR: "Network connectivity issues occurred",
            FailureCategory.API_ERROR: "API requests returned errors",
            FailureCategory.APP_CRASH: "Application crashed during tests",
            FailureCategory.RACE_CONDITION: "Possible race conditions detected",
            FailureCategory.SYSTEM_ALERT: "System alerts interfered with tests",
            FailureCategory.SNAPSHOT_MISMATCH: "Visual snapshots do not match references",
            FailureCategory.ACCESSIBILITY_MISSING: "Accessibility identifiers are missing",
            FailureCategory.MOCK_FAILURE: "Mock configuration issues",
        }
        return summaries.get(category, f"Issues categorized as {category.value}")

    def _get_category_explanation(self, category: FailureCategory) -> str:
        """Get detailed explanation for a category."""
        explanations = {
            FailureCategory.MISSING_ELEMENT: (
                "The test tried to interact with UI elements that could not be found. "
                "This could be due to: elements not being rendered yet, incorrect identifiers, "
                "navigation issues, or conditional UI not being displayed."
            ),
            FailureCategory.TIMEOUT: (
                "Operations waited longer than the allowed timeout period. "
                "This often indicates: slow network responses, animations taking too long, "
                "or conditions that never become true."
            ),
            FailureCategory.ASSERTION_FAILURE: (
                "Test assertions evaluated to false, indicating the application behavior "
                "does not match expected behavior. This may be a genuine bug or test issue."
            ),
            FailureCategory.APP_CRASH: (
                "The application terminated unexpectedly during test execution. "
                "This is a critical issue that requires immediate investigation."
            ),
            FailureCategory.RACE_CONDITION: (
                "Tests may have encountered timing-dependent failures where the order "
                "of operations affected the outcome. These are often flaky."
            ),
        }
        return explanations.get(category, f"Multiple tests failed with {category.value} issues.")

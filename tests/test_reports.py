"""Tests for report generators."""

import json
import pytest
from datetime import datetime
from pathlib import Path

from xcresult_ai_assistant.reports.console_reporter import ConsoleReporter
from xcresult_ai_assistant.reports.html_reporter import HtmlReporter
from xcresult_ai_assistant.reports.markdown_reporter import MarkdownReporter
from xcresult_ai_assistant.reports.json_reporter import JsonReporter
from xcresult_ai_assistant.reports.report_factory import ReportFactory
from xcresult_ai_assistant.models.analysis import AnalysisResult, RootCauseAnalysis, DebugSuggestion, ConfidenceLevel
from xcresult_ai_assistant.models.failure import FailureCategory, FailureSeverity, TestFailure
from xcresult_ai_assistant.models.report import ReportConfig, ReportFormat


@pytest.fixture
def sample_analysis() -> AnalysisResult:
    """Create a sample analysis result."""
    return AnalysisResult(
        source_path="test.log",
        timestamp=datetime(2026, 5, 17, 10, 0, 0),
        total_tests=10,
        passed_tests=7,
        failed_tests=3,
        skipped_tests=0,
        failures=[
            TestFailure(
                test_name="testLogin",
                test_class="AuthTests",
                category=FailureCategory.TIMEOUT,
                severity=FailureSeverity.MEDIUM,
                message="Timed out waiting for login",
                is_flaky=True,
            ),
            TestFailure(
                test_name="testCrash",
                test_class="CoreTests",
                category=FailureCategory.APP_CRASH,
                severity=FailureSeverity.CRITICAL,
                message="EXC_BAD_ACCESS",
                is_app_issue=True,
            ),
            TestFailure(
                test_name="testButton",
                test_class="UITests",
                category=FailureCategory.MISSING_ELEMENT,
                severity=FailureSeverity.HIGH,
                message="Button not found",
                is_test_issue=True,
            ),
        ],
        root_causes=[
            RootCauseAnalysis(
                summary="Timeout issues detected",
                category=FailureCategory.TIMEOUT,
                confidence=ConfidenceLevel.HIGH,
                suggestions=[
                    DebugSuggestion(
                        title="Increase timeout",
                        description="The timeout may be too short",
                        action="Increase wait timeout to 10 seconds",
                    ),
                ],
            ),
        ],
        category_summary={
            "timeout": 1,
            "app_crash": 1,
            "missing_element": 1,
        },
        severity_summary={
            "critical": 1,
            "high": 1,
            "medium": 1,
        },
        flaky_count=1,
        app_bugs_count=1,
        analysis_duration=0.5,
    )


class TestConsoleReporter:
    """Tests for ConsoleReporter."""

    def test_generate_report(self, sample_analysis: AnalysisResult) -> None:
        """Test basic report generation."""
        reporter = ConsoleReporter()
        report = reporter.generate(sample_analysis)

        assert report.format == ReportFormat.CONSOLE
        assert report.analysis == sample_analysis
        assert report.content is not None

    def test_report_sections(self, sample_analysis: AnalysisResult) -> None:
        """Test report has expected sections."""
        reporter = ConsoleReporter()
        report = reporter.generate(sample_analysis)

        assert "summary" in report.sections
        assert "failures" in report.sections


class TestMarkdownReporter:
    """Tests for MarkdownReporter."""

    def test_generate_report(self, sample_analysis: AnalysisResult) -> None:
        """Test markdown report generation."""
        reporter = MarkdownReporter()
        report = reporter.generate(sample_analysis)

        assert report.format == ReportFormat.MARKDOWN
        assert "# " in report.content  # Has markdown headers
        assert "## " in report.content

    def test_report_contains_stats(self, sample_analysis: AnalysisResult) -> None:
        """Test report contains statistics."""
        reporter = MarkdownReporter()
        report = reporter.generate(sample_analysis)

        assert "10" in report.content  # Total tests
        assert "7" in report.content  # Passed
        assert "3" in report.content  # Failed
        assert "70.0%" in report.content  # Pass rate

    def test_report_contains_failures(self, sample_analysis: AnalysisResult) -> None:
        """Test report contains failure details."""
        reporter = MarkdownReporter()
        report = reporter.generate(sample_analysis)

        assert "testLogin" in report.content
        assert "testCrash" in report.content
        assert "testButton" in report.content

    def test_report_contains_categories(self, sample_analysis: AnalysisResult) -> None:
        """Test report contains category breakdown."""
        config = ReportConfig(format=ReportFormat.MARKDOWN, group_by_category=True)
        reporter = MarkdownReporter(config)
        report = reporter.generate(sample_analysis)

        assert "timeout" in report.content
        assert "app_crash" in report.content

    def test_report_contains_suggestions(self, sample_analysis: AnalysisResult) -> None:
        """Test report contains suggestions."""
        config = ReportConfig(format=ReportFormat.MARKDOWN, include_suggestions=True)
        reporter = MarkdownReporter(config)
        report = reporter.generate(sample_analysis)

        assert "Suggestion" in report.content or "suggestion" in report.content
        assert "Increase timeout" in report.content


class TestJsonReporter:
    """Tests for JsonReporter."""

    def test_generate_report(self, sample_analysis: AnalysisResult) -> None:
        """Test JSON report generation."""
        reporter = JsonReporter()
        report = reporter.generate(sample_analysis)

        assert report.format == ReportFormat.JSON
        # Should be valid JSON
        data = json.loads(report.content)
        assert "report" in data
        assert "summary" in data

    def test_json_structure(self, sample_analysis: AnalysisResult) -> None:
        """Test JSON has expected structure."""
        reporter = JsonReporter()
        report = reporter.generate(sample_analysis)
        data = json.loads(report.content)

        assert data["summary"]["total_tests"] == 10
        assert data["summary"]["passed"] == 7
        assert data["summary"]["failed"] == 3
        assert data["summary"]["pass_rate"] == 70.0

    def test_json_failures(self, sample_analysis: AnalysisResult) -> None:
        """Test JSON contains failures."""
        reporter = JsonReporter()
        report = reporter.generate(sample_analysis)
        data = json.loads(report.content)

        assert "failures" in data
        assert len(data["failures"]) == 3

        failure_names = [f["test_name"] for f in data["failures"]]
        assert "testLogin" in failure_names
        assert "testCrash" in failure_names

    def test_generate_minimal(self, sample_analysis: AnalysisResult) -> None:
        """Test minimal JSON generation."""
        reporter = JsonReporter()
        minimal = reporter.generate_minimal(sample_analysis)
        data = json.loads(minimal)

        assert data["status"] == "failed"
        assert data["total"] == 10
        assert data["pass_rate"] == 70.0

    def test_generate_failures_only(self, sample_analysis: AnalysisResult) -> None:
        """Test failures-only JSON generation."""
        reporter = JsonReporter()
        failures_json = reporter.generate_failures_only(sample_analysis)
        data = json.loads(failures_json)

        assert "failures" in data
        assert len(data["failures"]) == 3


class TestHtmlReporter:
    """Tests for HtmlReporter."""

    def test_generate_report(self, sample_analysis: AnalysisResult) -> None:
        """Test HTML report generation."""
        reporter = HtmlReporter()
        report = reporter.generate(sample_analysis)

        assert report.format == ReportFormat.HTML
        assert "<!DOCTYPE html>" in report.content
        assert "<html" in report.content
        assert "</html>" in report.content

    def test_report_contains_stats(self, sample_analysis: AnalysisResult) -> None:
        """Test report contains statistics."""
        reporter = HtmlReporter()
        report = reporter.generate(sample_analysis)

        assert "10" in report.content  # Total tests
        assert "7" in report.content  # Passed
        assert "3" in report.content  # Failed
        assert "70.0%" in report.content  # Pass rate

    def test_report_contains_failures(self, sample_analysis: AnalysisResult) -> None:
        """Test report contains failure details."""
        reporter = HtmlReporter()
        report = reporter.generate(sample_analysis)

        assert "testLogin" in report.content
        assert "testCrash" in report.content
        assert "testButton" in report.content

    def test_report_contains_categories(self, sample_analysis: AnalysisResult) -> None:
        """Test report contains category breakdown."""
        config = ReportConfig(format=ReportFormat.HTML, group_by_category=True)
        reporter = HtmlReporter(config)
        report = reporter.generate(sample_analysis)

        assert "timeout" in report.content
        assert "app_crash" in report.content

    def test_report_has_css_styles(self, sample_analysis: AnalysisResult) -> None:
        """Test report has embedded CSS."""
        reporter = HtmlReporter()
        report = reporter.generate(sample_analysis)

        assert "<style>" in report.content
        assert "</style>" in report.content
        assert "stat-card" in report.content

    def test_report_has_sections(self, sample_analysis: AnalysisResult) -> None:
        """Test report has expected sections."""
        reporter = HtmlReporter()
        report = reporter.generate(sample_analysis)

        assert "summary" in report.sections
        assert "stats" in report.sections
        assert "failures" in report.sections

    def test_report_escapes_html(self, sample_analysis: AnalysisResult) -> None:
        """Test report properly escapes HTML in content."""
        # Modify a failure message to include HTML-like content
        sample_analysis.failures[0].message = "<script>alert('xss')</script>"
        reporter = HtmlReporter()
        report = reporter.generate(sample_analysis)

        # Should be escaped
        assert "&lt;script&gt;" in report.content
        assert "<script>alert" not in report.content


class TestReportFactory:
    """Tests for ReportFactory."""

    def test_create_console_reporter(self) -> None:
        """Test creating console reporter."""
        reporter = ReportFactory.create_reporter(ReportFormat.CONSOLE)
        assert isinstance(reporter, ConsoleReporter)

    def test_create_markdown_reporter(self) -> None:
        """Test creating markdown reporter."""
        reporter = ReportFactory.create_reporter(ReportFormat.MARKDOWN)
        assert isinstance(reporter, MarkdownReporter)

    def test_create_json_reporter(self) -> None:
        """Test creating JSON reporter."""
        reporter = ReportFactory.create_reporter(ReportFormat.JSON)
        assert isinstance(reporter, JsonReporter)

    def test_create_html_reporter(self) -> None:
        """Test creating HTML reporter."""
        reporter = ReportFactory.create_reporter(ReportFormat.HTML)
        assert isinstance(reporter, HtmlReporter)

    def test_generate_report(self, sample_analysis: AnalysisResult) -> None:
        """Test generate_report factory method."""
        report = ReportFactory.generate_report(sample_analysis, ReportFormat.JSON)
        assert report.format == ReportFormat.JSON

    def test_generate_and_save(self, sample_analysis: AnalysisResult, tmp_path: Path) -> None:
        """Test generate_and_save."""
        output_path = tmp_path / "report.md"
        report = ReportFactory.generate_and_save(
            sample_analysis, output_path, ReportFormat.MARKDOWN
        )

        assert output_path.exists()
        content = output_path.read_text()
        assert "# " in content

    def test_detect_format_from_extension(self, sample_analysis: AnalysisResult, tmp_path: Path) -> None:
        """Test format detection from file extension."""
        md_path = tmp_path / "report.md"
        ReportFactory.generate_and_save(sample_analysis, md_path)
        assert md_path.exists()
        assert "# " in md_path.read_text()

        json_path = tmp_path / "report.json"
        ReportFactory.generate_and_save(sample_analysis, json_path)
        assert json_path.exists()
        data = json.loads(json_path.read_text())
        assert "summary" in data

    def test_generate_all_formats(self, sample_analysis: AnalysisResult, tmp_path: Path) -> None:
        """Test generating all formats."""
        reports = ReportFactory.generate_all_formats(
            sample_analysis, tmp_path, "test_report"
        )

        assert ReportFormat.MARKDOWN in reports
        assert ReportFormat.JSON in reports
        assert ReportFormat.HTML in reports

        assert (tmp_path / "test_report.md").exists()
        assert (tmp_path / "test_report.json").exists()
        assert (tmp_path / "test_report.html").exists()

    def test_detect_html_format(self, sample_analysis: AnalysisResult, tmp_path: Path) -> None:
        """Test format detection for HTML extension."""
        html_path = tmp_path / "report.html"
        ReportFactory.generate_and_save(sample_analysis, html_path)
        assert html_path.exists()
        assert "<!DOCTYPE html>" in html_path.read_text()

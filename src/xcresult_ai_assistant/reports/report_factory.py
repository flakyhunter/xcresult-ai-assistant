"""Factory for creating report generators."""

from __future__ import annotations

from pathlib import Path

from xcresult_ai_assistant.models.analysis import AnalysisResult
from xcresult_ai_assistant.models.report import AnalysisReport, ReportConfig, ReportFormat
from xcresult_ai_assistant.reports.console_reporter import ConsoleReporter
from xcresult_ai_assistant.reports.html_reporter import HtmlReporter
from xcresult_ai_assistant.reports.json_reporter import JsonReporter
from xcresult_ai_assistant.reports.markdown_reporter import MarkdownReporter


class ReportFactory:
    """Factory for creating and managing report generators."""

    @staticmethod
    def create_reporter(
        format: ReportFormat,
        config: ReportConfig | None = None,
    ) -> ConsoleReporter | MarkdownReporter | JsonReporter | HtmlReporter:
        """Create a reporter for the given format."""
        if config is None:
            config = ReportConfig(format=format)

        reporters = {
            ReportFormat.CONSOLE: ConsoleReporter,
            ReportFormat.MARKDOWN: MarkdownReporter,
            ReportFormat.JSON: JsonReporter,
            ReportFormat.HTML: HtmlReporter,
        }

        reporter_class = reporters.get(format, ConsoleReporter)
        return reporter_class(config)

    @staticmethod
    def generate_report(
        analysis: AnalysisResult,
        format: ReportFormat = ReportFormat.CONSOLE,
        config: ReportConfig | None = None,
    ) -> AnalysisReport:
        """Generate a report for the analysis result."""
        reporter = ReportFactory.create_reporter(format, config)
        return reporter.generate(analysis)

    @staticmethod
    def generate_and_save(
        analysis: AnalysisResult,
        output_path: Path | str,
        format: ReportFormat | None = None,
        config: ReportConfig | None = None,
    ) -> AnalysisReport:
        """Generate and save a report to a file."""
        output_path = Path(output_path)

        # Auto-detect format from extension if not specified
        if format is None:
            format = ReportFactory._detect_format(output_path)

        if config is None:
            config = ReportConfig(format=format, output_path=str(output_path))

        reporter = ReportFactory.create_reporter(format, config)
        report = reporter.generate(analysis)

        # Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report.content)

        return report

    @staticmethod
    def _detect_format(path: Path) -> ReportFormat:
        """Detect report format from file extension."""
        suffix = path.suffix.lower()
        format_map = {
            ".md": ReportFormat.MARKDOWN,
            ".markdown": ReportFormat.MARKDOWN,
            ".json": ReportFormat.JSON,
            ".html": ReportFormat.HTML,
            ".txt": ReportFormat.CONSOLE,
        }
        return format_map.get(suffix, ReportFormat.CONSOLE)

    @staticmethod
    def print_console_report(analysis: AnalysisResult, config: ReportConfig | None = None) -> None:
        """Print a report directly to console."""
        reporter = ConsoleReporter(config)
        reporter.print(analysis)

    @staticmethod
    def generate_all_formats(
        analysis: AnalysisResult,
        output_dir: Path | str,
        base_name: str = "report",
        config: ReportConfig | None = None,
    ) -> dict[ReportFormat, AnalysisReport]:
        """Generate reports in all supported formats."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        reports = {}

        # Generate each format
        formats_and_extensions = [
            (ReportFormat.MARKDOWN, ".md"),
            (ReportFormat.JSON, ".json"),
            (ReportFormat.HTML, ".html"),
        ]

        for format, extension in formats_and_extensions:
            output_path = output_dir / f"{base_name}{extension}"
            report = ReportFactory.generate_and_save(
                analysis, output_path, format, config
            )
            reports[format] = report

        return reports

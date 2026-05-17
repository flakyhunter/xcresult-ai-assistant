"""Console reporter using Rich for beautiful terminal output."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from xcresult_ai_assistant.models.analysis import AnalysisResult
from xcresult_ai_assistant.models.failure import FailureSeverity
from xcresult_ai_assistant.models.report import AnalysisReport, ReportConfig, ReportFormat


class ConsoleReporter:
    """Reporter for console output using Rich."""

    def __init__(self, config: ReportConfig | None = None):
        """Initialize reporter."""
        self.config = config or ReportConfig(format=ReportFormat.CONSOLE)
        self.console = Console()

    def generate(self, analysis: AnalysisResult) -> AnalysisReport:
        """Generate console report."""
        sections: dict[str, str] = {}

        # Generate each section
        sections["summary"] = self._generate_summary(analysis)
        sections["failures"] = self._generate_failures(analysis)

        if self.config.include_suggestions and analysis.root_causes:
            sections["suggestions"] = self._generate_suggestions(analysis)

        if self.config.group_by_category:
            sections["categories"] = self._generate_categories(analysis)

        # The content is rendered directly to console
        content = "\n".join(sections.values())

        return AnalysisReport(
            title=self.config.title,
            format=ReportFormat.CONSOLE,
            analysis=analysis,
            config=self.config,
            content=content,
            sections=sections,
        )

    def print(self, analysis: AnalysisResult) -> None:
        """Print report directly to console."""
        self._print_header(analysis)
        self._print_summary(analysis)

        if analysis.failures:
            self._print_failures(analysis)

            if self.config.group_by_category:
                self._print_categories(analysis)

            if self.config.include_suggestions:
                self._print_suggestions(analysis)

        self._print_footer(analysis)

    def _print_header(self, analysis: AnalysisResult) -> None:
        """Print report header."""
        title = Text(self.config.title, style="bold blue")
        self.console.print()
        self.console.print(Panel(title, expand=False))
        self.console.print()

    def _print_summary(self, analysis: AnalysisResult) -> None:
        """Print summary statistics."""
        # Create summary table
        table = Table(title="Test Summary", show_header=True, header_style="bold")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")

        # Status indicator
        if analysis.failed_tests == 0:
            status = Text("✅ ALL PASSED", style="bold green")
        else:
            status = Text(f"❌ {analysis.failed_tests} FAILURES", style="bold red")

        table.add_row("Status", status)
        table.add_row("Total Tests", str(analysis.total_tests))
        table.add_row("Passed", Text(str(analysis.passed_tests), style="green"))
        table.add_row("Failed", Text(str(analysis.failed_tests), style="red"))
        table.add_row("Skipped", Text(str(analysis.skipped_tests), style="yellow"))

        if self.config.show_pass_rate:
            pass_rate = f"{analysis.pass_rate:.1f}%"
            style = "green" if analysis.pass_rate >= 90 else "yellow" if analysis.pass_rate >= 70 else "red"
            table.add_row("Pass Rate", Text(pass_rate, style=style))

        if self.config.show_timing:
            table.add_row("Analysis Time", f"{analysis.analysis_duration:.2f}s")

        self.console.print(table)
        self.console.print()

    def _print_failures(self, analysis: AnalysisResult) -> None:
        """Print failure details."""
        self.console.print("[bold red]Failures:[/bold red]")
        self.console.print()

        failures = analysis.prioritized_failures
        if self.config.max_failures:
            failures = failures[: self.config.max_failures]

        for i, failure in enumerate(failures, 1):
            self._print_failure(failure, i)

        if len(analysis.failures) > self.config.max_failures:
            remaining = len(analysis.failures) - self.config.max_failures
            self.console.print(f"[dim]... and {remaining} more failures[/dim]")
            self.console.print()

    def _print_failure(self, failure: "TestFailure", index: int) -> None:
        """Print a single failure."""
        from xcresult_ai_assistant.models.failure import TestFailure

        # Severity color
        severity_colors = {
            FailureSeverity.CRITICAL: "bold red",
            FailureSeverity.HIGH: "red",
            FailureSeverity.MEDIUM: "yellow",
            FailureSeverity.LOW: "blue",
            FailureSeverity.INFO: "dim",
        }
        severity_style = severity_colors.get(failure.severity, "white")

        # Build failure tree
        tree = Tree(f"[bold]{index}. {failure.full_name}[/bold]")
        tree.add(f"[{severity_style}]Severity: {failure.severity.value.upper()}[/{severity_style}]")
        tree.add(f"Category: {failure.category.value}")

        if failure.message:
            msg = failure.message[:200] + "..." if len(failure.message) > 200 else failure.message
            tree.add(f"Message: {msg}")

        if failure.location != "unknown":
            tree.add(f"Location: {failure.location}")

        # Flaky indicator
        if self.config.show_flaky_indicators and failure.is_flaky:
            tree.add("[yellow]⚠️ Likely flaky[/yellow]")

        if failure.is_app_issue:
            tree.add("[red]🐛 Likely app bug[/red]")
        elif failure.is_infrastructure:
            tree.add("[blue]🔧 Infrastructure issue[/blue]")
        elif failure.is_test_issue:
            tree.add("[cyan]🧪 Test code issue[/cyan]")

        # Stack trace (if enabled and not too long)
        if self.config.include_stack_traces and failure.stack_trace:
            trace = failure.stack_trace[:500]
            if len(failure.stack_trace) > 500:
                trace += "..."
            tree.add(f"[dim]Stack trace:\n{trace}[/dim]")

        self.console.print(tree)
        self.console.print()

    def _print_categories(self, analysis: AnalysisResult) -> None:
        """Print category breakdown."""
        if not analysis.category_summary:
            return

        self.console.print("[bold]Failures by Category:[/bold]")

        table = Table(show_header=True, header_style="bold")
        table.add_column("Category")
        table.add_column("Count", justify="right")
        table.add_column("Percentage", justify="right")

        total = sum(analysis.category_summary.values())
        for category, count in analysis.top_categories:
            pct = (count / total * 100) if total > 0 else 0
            table.add_row(category, str(count), f"{pct:.1f}%")

        self.console.print(table)
        self.console.print()

    def _print_suggestions(self, analysis: AnalysisResult) -> None:
        """Print debugging suggestions."""
        if not analysis.root_causes:
            return

        self.console.print("[bold green]Debugging Suggestions:[/bold green]")
        self.console.print()

        for rca in analysis.root_causes[:5]:
            self.console.print(f"[bold]{rca.summary}[/bold]")

            if rca.suggestions:
                for suggestion in rca.suggestions[:2]:
                    self.console.print(f"  → {suggestion.title}")
                    if suggestion.action:
                        self.console.print(f"    [dim]{suggestion.action}[/dim]")

            self.console.print()

    def _print_footer(self, analysis: AnalysisResult) -> None:
        """Print report footer."""
        self.console.print(f"[dim]Source: {analysis.source_path}[/dim]")
        self.console.print(f"[dim]Generated at: {analysis.timestamp.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")

    def _generate_summary(self, analysis: AnalysisResult) -> str:
        """Generate summary text."""
        lines = [
            f"Total: {analysis.total_tests} tests",
            f"Passed: {analysis.passed_tests}",
            f"Failed: {analysis.failed_tests}",
            f"Pass Rate: {analysis.pass_rate:.1f}%",
        ]
        return "\n".join(lines)

    def _generate_failures(self, analysis: AnalysisResult) -> str:
        """Generate failures text."""
        lines = []
        for failure in analysis.failures[: self.config.max_failures]:
            lines.append(f"- {failure.full_name}: {failure.category.value}")
        return "\n".join(lines)

    def _generate_suggestions(self, analysis: AnalysisResult) -> str:
        """Generate suggestions text."""
        lines = []
        for rca in analysis.root_causes:
            lines.append(f"- {rca.summary}")
        return "\n".join(lines)

    def _generate_categories(self, analysis: AnalysisResult) -> str:
        """Generate categories text."""
        lines = []
        for category, count in analysis.top_categories:
            lines.append(f"- {category}: {count}")
        return "\n".join(lines)

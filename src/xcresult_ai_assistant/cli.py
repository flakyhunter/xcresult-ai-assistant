"""Command-line interface for xcresult-ai-assistant."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from xcresult_ai_assistant import __version__
from xcresult_ai_assistant.analyzers.failure_analyzer import FailureAnalyzer
from xcresult_ai_assistant.analyzers.flaky_detector import FlakyDetector
from xcresult_ai_assistant.models.report import ReportConfig, ReportFormat
from xcresult_ai_assistant.parsers.auto_parser import AutoParser
from xcresult_ai_assistant.reports.report_factory import ReportFactory
from xcresult_ai_assistant.utils.file_utils import (
    find_log_files,
    find_xcresult_bundles,
    is_supported_file,
)

app = typer.Typer(
    name="xcresult-ai",
    help="AI-powered assistant for analyzing xcresult bundles and XCTest failures.",
    add_completion=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option("--version", "-v", help="Show version and exit"),
    ] = False,
) -> None:
    """XCResult AI Assistant - Analyze test failures with AI-powered insights."""
    if version:
        print(f"xcresult-ai-assistant v{__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())


@app.command()
def analyze(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to xcresult bundle, log file, or directory",
            exists=True,
        ),
    ],
    format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: console, markdown, json"),
    ] = "console",
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Output file path"),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-V", help="Verbose output"),
    ] = False,
    suggestions: Annotated[
        bool,
        typer.Option("--suggestions/--no-suggestions", help="Include debugging suggestions"),
    ] = True,
    stack_traces: Annotated[
        bool,
        typer.Option("--stack-traces/--no-stack-traces", help="Include stack traces"),
    ] = False,
    max_failures: Annotated[
        int,
        typer.Option("--max-failures", "-m", help="Maximum failures to show"),
    ] = 50,
    group_by_category: Annotated[
        bool,
        typer.Option("--group/--no-group", help="Group failures by category"),
    ] = True,
) -> None:
    """Analyze test results and generate a report.

    Examples:
        xcresult-ai analyze results.xcresult
        xcresult-ai analyze test-output.log --format markdown -o report.md
        xcresult-ai analyze ./logs/ --format json
    """
    # Validate format
    try:
        report_format = ReportFormat(format.lower())
    except ValueError:
        console.print(f"[red]Invalid format: {format}[/red]")
        console.print("Valid formats: console, markdown, json")
        raise typer.Exit(1)

    # Parse input
    parser = AutoParser(verbose=verbose)

    if path.is_file():
        if not is_supported_file(path):
            console.print(f"[red]Unsupported file type: {path}[/red]")
            raise typer.Exit(1)

        if verbose:
            console.print(f"[dim]Parsing file: {path}[/dim]")

        result = parser.parse(path)

    elif path.is_dir():
        # Check if it's an xcresult bundle
        if path.suffix == ".xcresult":
            if verbose:
                console.print(f"[dim]Parsing xcresult bundle: {path}[/dim]")
            result = parser.parse(path)
        else:
            # Find and parse all test files in directory
            console.print(f"[dim]Scanning directory: {path}[/dim]")
            files = find_xcresult_bundles(path) + find_log_files(path)

            if not files:
                console.print("[yellow]No test files found in directory[/yellow]")
                raise typer.Exit(1)

            if verbose:
                console.print(f"[dim]Found {len(files)} files[/dim]")

            # Parse first file for now (could be extended to merge)
            result = parser.parse(files[0])
            if len(files) > 1:
                console.print(f"[dim]Note: Analyzed first file. Found {len(files)} total.[/dim]")
    else:
        console.print(f"[red]Path not found: {path}[/red]")
        raise typer.Exit(1)

    # Check parse result
    if not result.success or result.test_run is None:
        console.print("[red]Failed to parse test results[/red]")
        for error in result.errors:
            console.print(f"  [red]• {error}[/red]")
        raise typer.Exit(1)

    for warning in result.warnings:
        console.print(f"[yellow]Warning: {warning}[/yellow]")

    # Analyze failures
    if verbose:
        console.print("[dim]Analyzing failures...[/dim]")

    analyzer = FailureAnalyzer(verbose=verbose)
    analysis = analyzer.analyze(result.test_run)

    # Generate report
    config = ReportConfig(
        format=report_format,
        output_path=str(output) if output else "",
        include_suggestions=suggestions,
        include_stack_traces=stack_traces,
        max_failures=max_failures,
        group_by_category=group_by_category,
        verbose=verbose,
    )

    if output:
        report = ReportFactory.generate_and_save(analysis, output, report_format, config)
        console.print(f"[green]Report saved to: {output}[/green]")
    else:
        if report_format == ReportFormat.CONSOLE:
            ReportFactory.print_console_report(analysis, config)
        else:
            report = ReportFactory.generate_report(analysis, report_format, config)
            console.print(report.content)


@app.command()
def report(
    input_file: Annotated[
        Path,
        typer.Argument(help="Input JSON analysis file", exists=True),
    ],
    format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: console, markdown, json"),
    ] = "console",
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Output file path"),
    ] = None,
) -> None:
    """Generate a report from a previously saved analysis.

    Example:
        xcresult-ai report analysis.json --format markdown -o report.md
    """
    import json

    from xcresult_ai_assistant.models.analysis import AnalysisResult

    try:
        data = json.loads(input_file.read_text())

        # Try to reconstruct analysis from saved JSON
        if "analysis" in data:
            # It's a full report
            analysis_data = data["analysis"]
        else:
            # Assume it's the analysis itself
            analysis_data = data

        # For now, just re-parse if needed
        console.print("[yellow]Note: Regenerating report from JSON is limited[/yellow]")
        console.print(json.dumps(analysis_data, indent=2)[:1000])

    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON file: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error reading file: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def summarize(
    directory: Annotated[
        Path,
        typer.Argument(help="Directory containing test results", exists=True),
    ],
    recursive: Annotated[
        bool,
        typer.Option("--recursive", "-r", help="Search recursively"),
    ] = True,
) -> None:
    """Summarize test results from a directory.

    Example:
        xcresult-ai summarize ./test-results/
    """
    from rich.table import Table

    # Find all test files
    xcresults = find_xcresult_bundles(directory, recursive)
    logs = find_log_files(directory, recursive)
    all_files = xcresults + logs

    if not all_files:
        console.print("[yellow]No test files found[/yellow]")
        raise typer.Exit(1)

    console.print(f"[bold]Found {len(all_files)} test result files[/bold]")
    console.print()

    # Create summary table
    table = Table(title="Test Results Summary")
    table.add_column("File", style="cyan")
    table.add_column("Type")
    table.add_column("Tests", justify="right")
    table.add_column("Passed", justify="right", style="green")
    table.add_column("Failed", justify="right", style="red")
    table.add_column("Pass Rate", justify="right")

    parser = AutoParser()
    total_tests = 0
    total_passed = 0
    total_failed = 0

    for file_path in all_files[:20]:  # Limit to first 20
        result = parser.parse(file_path)

        if result.success and result.test_run:
            run = result.test_run
            file_type = "xcresult" if file_path.suffix == ".xcresult" else "log"

            total_tests += run.total_count
            total_passed += run.passed_count
            total_failed += run.failed_count

            rate = f"{run.pass_rate:.1f}%"
            rate_style = "green" if run.pass_rate >= 90 else "yellow" if run.pass_rate >= 70 else "red"

            table.add_row(
                file_path.name,
                file_type,
                str(run.total_count),
                str(run.passed_count),
                str(run.failed_count),
                f"[{rate_style}]{rate}[/{rate_style}]",
            )
        else:
            table.add_row(
                file_path.name,
                "error",
                "-",
                "-",
                "-",
                "[red]Parse failed[/red]",
            )

    console.print(table)

    if len(all_files) > 20:
        console.print(f"[dim]... and {len(all_files) - 20} more files[/dim]")

    # Print totals
    console.print()
    overall_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    console.print(f"[bold]Total:[/bold] {total_tests} tests, "
                  f"[green]{total_passed} passed[/green], "
                  f"[red]{total_failed} failed[/red], "
                  f"[{'green' if overall_rate >= 90 else 'yellow' if overall_rate >= 70 else 'red'}]"
                  f"{overall_rate:.1f}% pass rate[/]")


@app.command()
def flaky(
    path: Annotated[
        Path,
        typer.Argument(help="Path to test results", exists=True),
    ],
) -> None:
    """Detect potentially flaky tests.

    Example:
        xcresult-ai flaky results.xcresult
    """
    from rich.table import Table

    parser = AutoParser()
    result = parser.parse(path)

    if not result.success or result.test_run is None:
        console.print("[red]Failed to parse test results[/red]")
        raise typer.Exit(1)

    analyzer = FailureAnalyzer()
    analysis = analyzer.analyze(result.test_run)

    detector = FlakyDetector()
    summary = detector.get_flaky_summary(analysis.failures)

    console.print("[bold]Flaky Test Analysis[/bold]")
    console.print()

    # Stats
    console.print(f"Total failures analyzed: {summary['total_failures']}")
    console.print(f"Likely flaky: [yellow]{summary['likely_flaky']}[/yellow] "
                  f"({summary['flaky_percentage']:.1f}%)")
    console.print()

    if summary["indicators"]:
        console.print("[bold]Detected Patterns:[/bold]")
        for indicator in summary["indicators"]:
            console.print(f"  • {indicator}")
        console.print()

    if summary["recommendations"]:
        console.print("[bold green]Recommendations:[/bold green]")
        for rec in summary["recommendations"]:
            console.print(f"  → {rec}")
        console.print()

    # List flaky tests
    flaky_tests = [f for f in analysis.failures if f.is_flaky]
    if flaky_tests:
        table = Table(title="Potentially Flaky Tests")
        table.add_column("Test", style="cyan")
        table.add_column("Category")
        table.add_column("Score", justify="right")

        for failure in flaky_tests[:20]:
            score = detector.calculate_flaky_score(failure)
            table.add_row(
                failure.full_name,
                failure.category.value,
                f"{score:.2f}",
            )

        console.print(table)


@app.command()
def categories(
    path: Annotated[
        Path,
        typer.Argument(help="Path to test results", exists=True),
    ],
) -> None:
    """Show failure categories breakdown.

    Example:
        xcresult-ai categories results.xcresult
    """
    from rich.table import Table

    parser = AutoParser()
    result = parser.parse(path)

    if not result.success or result.test_run is None:
        console.print("[red]Failed to parse test results[/red]")
        raise typer.Exit(1)

    analyzer = FailureAnalyzer()
    analysis = analyzer.analyze(result.test_run)

    if not analysis.category_summary:
        console.print("[yellow]No failures to categorize[/yellow]")
        raise typer.Exit(0)

    console.print("[bold]Failure Categories Breakdown[/bold]")
    console.print()

    table = Table()
    table.add_column("Category", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Percentage", justify="right")
    table.add_column("Description")

    total = sum(analysis.category_summary.values())

    # Category descriptions
    descriptions = {
        "missing_element": "UI element not found",
        "timeout": "Operation timed out",
        "wait_timeout": "Wait condition not met",
        "assertion_failure": "Test assertion failed",
        "app_crash": "Application crashed",
        "network_error": "Network connectivity issue",
        "system_alert": "System dialog interference",
        "snapshot_mismatch": "Visual comparison failed",
        "race_condition": "Timing/race issue",
    }

    for category, count in analysis.top_categories:
        pct = (count / total * 100) if total > 0 else 0
        desc = descriptions.get(category, "")
        table.add_row(category, str(count), f"{pct:.1f}%", desc)

    console.print(table)


@app.command()
def info() -> None:
    """Show tool information and capabilities."""
    from rich.panel import Panel

    info_text = f"""[bold blue]XCResult AI Assistant[/bold blue]
Version: {__version__}

[bold]Supported Input Formats:[/bold]
  • .xcresult bundles (Xcode test results)
  • .log / .txt files (XCTest console output)
  • .xml files (JUnit format)

[bold]Failure Categories Detected:[/bold]
  • Missing/not hittable UI elements
  • Timeout and wait issues
  • Assertion failures
  • App crashes
  • Network errors
  • Race conditions
  • System alert interference
  • Snapshot mismatches
  • Accessibility issues
  • Mock/fixture problems

[bold]Output Formats:[/bold]
  • Console (rich terminal output)
  • Markdown (for documentation/PRs)
  • JSON (for CI/CD integration)

[bold]Commands:[/bold]
  analyze     Analyze test results
  summarize   Summarize multiple result files
  flaky       Detect flaky tests
  categories  Show failure breakdown
  report      Generate report from JSON

[dim]Run 'xcresult-ai <command> --help' for more info[/dim]"""

    console.print(Panel(info_text, title="xcresult-ai", expand=False))


if __name__ == "__main__":
    app()

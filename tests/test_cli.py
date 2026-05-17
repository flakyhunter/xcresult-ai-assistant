"""Tests for CLI commands."""

import pytest
from pathlib import Path
from typer.testing import CliRunner

from xcresult_ai_assistant.cli import app


runner = CliRunner()


class TestCLI:
    """Tests for CLI commands."""

    @pytest.fixture
    def examples_dir(self) -> Path:
        """Get examples directory."""
        return Path(__file__).parent.parent / "examples"

    def test_version(self) -> None:
        """Test version command."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "xcresult-ai-assistant" in result.output

    def test_info(self) -> None:
        """Test info command."""
        result = runner.invoke(app, ["info"])
        assert result.exit_code == 0
        assert "XCResult AI Assistant" in result.stdout
        assert "analyze" in result.stdout
        assert "summarize" in result.stdout

    def test_analyze_log_file(self, examples_dir: Path) -> None:
        """Test analyzing a log file."""
        log_file = examples_dir / "sample_xctest_log.txt"
        if not log_file.exists():
            pytest.skip("Example file not found")

        result = runner.invoke(app, ["analyze", str(log_file)])
        assert result.exit_code == 0
        assert "Test" in result.stdout

    def test_analyze_junit_file(self, examples_dir: Path) -> None:
        """Test analyzing a JUnit XML file."""
        xml_file = examples_dir / "sample_junit.xml"
        if not xml_file.exists():
            pytest.skip("Example file not found")

        result = runner.invoke(app, ["analyze", str(xml_file)])
        assert result.exit_code == 0
        assert "Test" in result.stdout

    def test_analyze_passing_tests(self, examples_dir: Path) -> None:
        """Test analyzing passing tests."""
        log_file = examples_dir / "passing_tests.txt"
        if not log_file.exists():
            pytest.skip("Example file not found")

        result = runner.invoke(app, ["analyze", str(log_file)])
        assert result.exit_code == 0
        assert "PASSED" in result.stdout or "100" in result.stdout

    def test_analyze_with_markdown_output(self, examples_dir: Path, tmp_path: Path) -> None:
        """Test analyzing with markdown output."""
        log_file = examples_dir / "sample_xctest_log.txt"
        if not log_file.exists():
            pytest.skip("Example file not found")

        output_file = tmp_path / "report.md"
        result = runner.invoke(app, [
            "analyze", str(log_file),
            "--format", "markdown",
            "--output", str(output_file),
        ])

        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "# " in content

    def test_analyze_with_json_output(self, examples_dir: Path, tmp_path: Path) -> None:
        """Test analyzing with JSON output."""
        log_file = examples_dir / "sample_xctest_log.txt"
        if not log_file.exists():
            pytest.skip("Example file not found")

        output_file = tmp_path / "report.json"
        result = runner.invoke(app, [
            "analyze", str(log_file),
            "--format", "json",
            "--output", str(output_file),
        ])

        assert result.exit_code == 0
        assert output_file.exists()

        import json
        data = json.loads(output_file.read_text())
        assert "summary" in data

    def test_analyze_nonexistent_file(self) -> None:
        """Test analyzing nonexistent file."""
        result = runner.invoke(app, ["analyze", "/nonexistent/path.log"])
        assert result.exit_code != 0

    def test_analyze_with_verbose(self, examples_dir: Path) -> None:
        """Test analyze with verbose flag."""
        log_file = examples_dir / "passing_tests.txt"
        if not log_file.exists():
            pytest.skip("Example file not found")

        result = runner.invoke(app, ["analyze", str(log_file), "--verbose"])
        assert result.exit_code == 0

    def test_analyze_no_suggestions(self, examples_dir: Path) -> None:
        """Test analyze without suggestions."""
        log_file = examples_dir / "sample_xctest_log.txt"
        if not log_file.exists():
            pytest.skip("Example file not found")

        result = runner.invoke(app, [
            "analyze", str(log_file),
            "--no-suggestions",
        ])
        assert result.exit_code == 0

    def test_summarize_directory(self, examples_dir: Path) -> None:
        """Test summarize command."""
        if not examples_dir.exists():
            pytest.skip("Examples directory not found")

        result = runner.invoke(app, ["summarize", str(examples_dir)])
        assert result.exit_code == 0
        assert "Found" in result.stdout

    def test_flaky_command(self, examples_dir: Path) -> None:
        """Test flaky detection command."""
        log_file = examples_dir / "sample_xctest_log.txt"
        if not log_file.exists():
            pytest.skip("Example file not found")

        result = runner.invoke(app, ["flaky", str(log_file)])
        assert result.exit_code == 0
        assert "Flaky" in result.stdout

    def test_categories_command(self, examples_dir: Path) -> None:
        """Test categories command."""
        log_file = examples_dir / "sample_xctest_log.txt"
        if not log_file.exists():
            pytest.skip("Example file not found")

        result = runner.invoke(app, ["categories", str(log_file)])
        assert result.exit_code == 0
        assert "Category" in result.stdout or "category" in result.stdout

    def test_invalid_format(self, examples_dir: Path) -> None:
        """Test invalid format option."""
        log_file = examples_dir / "passing_tests.txt"
        if not log_file.exists():
            pytest.skip("Example file not found")

        result = runner.invoke(app, [
            "analyze", str(log_file),
            "--format", "invalid_format",
        ])
        assert result.exit_code != 0
        assert "Invalid format" in result.stdout

    def test_analyze_with_html_output(self, examples_dir: Path, tmp_path: Path) -> None:
        """Test analyzing with HTML output."""
        log_file = examples_dir / "sample_xctest_log.txt"
        if not log_file.exists():
            pytest.skip("Example file not found")

        output_file = tmp_path / "report.html"
        result = runner.invoke(app, [
            "analyze", str(log_file),
            "--format", "html",
            "--output", str(output_file),
        ])

        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "<!DOCTYPE html>" in content
        assert "<style>" in content

    def test_explain_command(self, examples_dir: Path) -> None:
        """Test explain command."""
        log_file = examples_dir / "sample_xctest_log.txt"
        if not log_file.exists():
            pytest.skip("Example file not found")

        result = runner.invoke(app, ["explain", str(log_file)])
        assert result.exit_code == 0
        assert "Analysis" in result.stdout or "Failure" in result.stdout

    def test_explain_with_top_option(self, examples_dir: Path) -> None:
        """Test explain command with --top option."""
        log_file = examples_dir / "sample_xctest_log.txt"
        if not log_file.exists():
            pytest.skip("Example file not found")

        result = runner.invoke(app, ["explain", str(log_file), "--top", "5"])
        assert result.exit_code == 0

    def test_explain_passing_tests(self, examples_dir: Path) -> None:
        """Test explain command with passing tests."""
        log_file = examples_dir / "passing_tests.txt"
        if not log_file.exists():
            pytest.skip("Example file not found")

        result = runner.invoke(app, ["explain", str(log_file)])
        assert result.exit_code == 0
        assert "passed" in result.stdout.lower() or "no failures" in result.stdout.lower()

    def test_info_shows_html_format(self) -> None:
        """Test that info command shows HTML format."""
        result = runner.invoke(app, ["info"])
        assert result.exit_code == 0
        assert "HTML" in result.stdout or "html" in result.stdout

    def test_info_shows_explain_command(self) -> None:
        """Test that info command shows explain command."""
        result = runner.invoke(app, ["info"])
        assert result.exit_code == 0
        assert "explain" in result.stdout


class TestCLIIntegration:
    """Integration tests for CLI."""

    @pytest.fixture
    def examples_dir(self) -> Path:
        """Get examples directory."""
        return Path(__file__).parent.parent / "examples"

    def test_full_workflow_log_to_markdown(
        self, examples_dir: Path, tmp_path: Path
    ) -> None:
        """Test full workflow from log to markdown report."""
        log_file = examples_dir / "sample_xctest_log.txt"
        if not log_file.exists():
            pytest.skip("Example file not found")

        output = tmp_path / "report.md"

        result = runner.invoke(app, [
            "analyze", str(log_file),
            "--format", "markdown",
            "--output", str(output),
            "--suggestions",
            "--group-by-category",
        ])

        assert result.exit_code == 0
        assert output.exists()

        content = output.read_text()
        assert "# " in content
        assert "Failure" in content or "failure" in content

    def test_full_workflow_junit_to_json(
        self, examples_dir: Path, tmp_path: Path
    ) -> None:
        """Test full workflow from JUnit XML to JSON report."""
        xml_file = examples_dir / "sample_junit.xml"
        if not xml_file.exists():
            pytest.skip("Example file not found")

        output = tmp_path / "report.json"

        result = runner.invoke(app, [
            "analyze", str(xml_file),
            "--format", "json",
            "--output", str(output),
        ])

        assert result.exit_code == 0
        assert output.exists()

        import json
        data = json.loads(output.read_text())
        assert "summary" in data
        assert "failures" in data

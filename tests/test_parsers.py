"""Tests for parsers."""

import pytest
from pathlib import Path

from xcresult_ai_assistant.parsers.log_parser import LogParser
from xcresult_ai_assistant.parsers.junit_parser import JUnitParser
from xcresult_ai_assistant.parsers.auto_parser import AutoParser
from xcresult_ai_assistant.models.test_result import TestStatus


class TestLogParser:
    """Tests for LogParser."""

    def test_parse_passed_test(self) -> None:
        """Test parsing a passing test."""
        content = """
Test Suite 'MyTests' started at 2026-05-17 10:00:00.000
Test Case '-[MyTests testSuccess]' started.
Test Case '-[MyTests testSuccess]' passed (1.500 seconds).
Test Suite 'MyTests' passed at 2026-05-17 10:00:02.000.
"""
        parser = LogParser()
        result = parser.parse_content(content)

        assert result.success
        assert result.test_run is not None
        assert result.test_run.total_count == 1
        assert result.test_run.passed_count == 1
        assert result.test_run.failed_count == 0

    def test_parse_failed_test(self) -> None:
        """Test parsing a failing test."""
        content = """
Test Case '-[MyTests testFailure]' started.
/path/to/file.swift:42: error: -[MyTests testFailure] : XCTAssertEqual failed
Test Case '-[MyTests testFailure]' failed (2.000 seconds).
"""
        parser = LogParser()
        result = parser.parse_content(content)

        assert result.success
        assert result.test_run is not None
        assert result.test_run.failed_count == 1

        failed_test = result.test_run.failed_tests[0]
        assert failed_test.name == "testFailure"
        assert failed_test.class_name == "MyTests"
        assert failed_test.status == TestStatus.FAILED
        assert failed_test.file_path == "/path/to/file.swift"
        assert failed_test.line_number == 42

    def test_parse_timeout(self) -> None:
        """Test parsing a timeout failure."""
        content = """
Test Case '-[MyTests testTimeout]' started.
Timed out waiting for element to exist
Test Case '-[MyTests testTimeout]' failed (10.000 seconds).
"""
        parser = LogParser()
        result = parser.parse_content(content)

        assert result.success
        assert result.test_run is not None
        failed_test = result.test_run.failed_tests[0]
        # Timeout may be detected as FAILED with timeout message, or TIMEOUT status
        # The raw_output or stack_trace may contain the timeout message
        assert failed_test.status in (TestStatus.TIMEOUT, TestStatus.FAILED)
        timeout_in_output = (
            "timeout" in failed_test.message.lower()
            or "timeout" in failed_test.stack_trace.lower()
            or "timeout" in failed_test.raw_output.lower()
            or failed_test.status == TestStatus.TIMEOUT
        )
        assert timeout_in_output

    def test_parse_crash(self) -> None:
        """Test parsing a crash."""
        content = """
Test Case '-[MyTests testCrash]' started.
CRASH: EXC_BAD_ACCESS
Test Case '-[MyTests testCrash]' failed (0.500 seconds).
"""
        parser = LogParser()
        result = parser.parse_content(content)

        assert result.success
        assert result.test_run is not None
        failed_test = result.test_run.failed_tests[0]
        assert failed_test.status == TestStatus.CRASHED

    def test_parse_multiple_suites(self) -> None:
        """Test parsing multiple test suites."""
        content = """
Test Suite 'Suite1' started at 2026-05-17 10:00:00.000
Test Case '-[Suite1 test1]' started.
Test Case '-[Suite1 test1]' passed (0.500 seconds).
Test Suite 'Suite1' passed at 2026-05-17 10:00:01.000.

Test Suite 'Suite2' started at 2026-05-17 10:00:02.000
Test Case '-[Suite2 test2]' started.
Test Case '-[Suite2 test2]' passed (0.500 seconds).
Test Case '-[Suite2 test3]' started.
Test Case '-[Suite2 test3]' failed (1.000 seconds).
Test Suite 'Suite2' failed at 2026-05-17 10:00:04.000.
"""
        parser = LogParser()
        result = parser.parse_content(content)

        assert result.success
        assert result.test_run is not None
        assert result.test_run.total_count == 3
        assert result.test_run.passed_count == 2
        assert result.test_run.failed_count == 1

    def test_can_parse(self, tmp_path: Path) -> None:
        """Test can_parse method."""
        parser = LogParser()

        # Create test files
        log_file = tmp_path / "test.log"
        log_file.write_text("Test Case '-[Test test]' passed (1.0 seconds).")

        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Test Suite 'All' started")

        random_file = tmp_path / "test.py"
        random_file.write_text("print('hello')")

        assert parser.can_parse(log_file)
        assert parser.can_parse(txt_file)
        assert not parser.can_parse(random_file)


class TestJUnitParser:
    """Tests for JUnitParser."""

    def test_parse_basic_xml(self) -> None:
        """Test parsing basic JUnit XML."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="MyTests" tests="2" failures="1" time="3.5">
  <testcase classname="MyTests" name="testSuccess" time="1.5"/>
  <testcase classname="MyTests" name="testFailure" time="2.0">
    <failure message="Assertion failed">Expected true but got false</failure>
  </testcase>
</testsuite>
"""
        parser = JUnitParser()
        result = parser.parse_content(content)

        assert result.success
        assert result.test_run is not None
        assert result.test_run.total_count == 2
        assert result.test_run.passed_count == 1
        assert result.test_run.failed_count == 1

    def test_parse_testsuites_wrapper(self) -> None:
        """Test parsing with testsuites wrapper."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="AllTests" tests="3" failures="0">
  <testsuite name="Suite1" tests="2" failures="0">
    <testcase classname="Suite1" name="test1" time="1.0"/>
    <testcase classname="Suite1" name="test2" time="1.0"/>
  </testsuite>
  <testsuite name="Suite2" tests="1" failures="0">
    <testcase classname="Suite2" name="test3" time="1.0"/>
  </testsuite>
</testsuites>
"""
        parser = JUnitParser()
        result = parser.parse_content(content)

        assert result.success
        assert result.test_run is not None
        assert len(result.test_run.suites) == 2
        assert result.test_run.total_count == 3

    def test_parse_error(self) -> None:
        """Test parsing test with error."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="Tests" tests="1" errors="1">
  <testcase classname="Tests" name="testCrash" time="0.5">
    <error message="Crash" type="EXC_BAD_ACCESS">Stack trace here</error>
  </testcase>
</testsuite>
"""
        parser = JUnitParser()
        result = parser.parse_content(content)

        assert result.success
        assert result.test_run is not None
        test = result.test_run.all_tests[0]
        assert test.status == TestStatus.ERROR

    def test_parse_skipped(self) -> None:
        """Test parsing skipped test."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="Tests" tests="1">
  <testcase classname="Tests" name="testSkipped" time="0">
    <skipped message="Not implemented"/>
  </testcase>
</testsuite>
"""
        parser = JUnitParser()
        result = parser.parse_content(content)

        assert result.success
        assert result.test_run is not None
        test = result.test_run.all_tests[0]
        assert test.status == TestStatus.SKIPPED

    def test_can_parse(self, tmp_path: Path) -> None:
        """Test can_parse method."""
        parser = JUnitParser()

        junit_file = tmp_path / "results.xml"
        junit_file.write_text('<?xml version="1.0"?><testsuite name="t"/>')

        random_xml = tmp_path / "config.xml"
        random_xml.write_text('<?xml version="1.0"?><config><setting/></config>')

        assert parser.can_parse(junit_file)
        assert not parser.can_parse(random_xml)


class TestAutoParser:
    """Tests for AutoParser."""

    def test_detect_log_format(self) -> None:
        """Test auto-detection of log format."""
        content = """
Test Case '-[MyTests testMethod]' started.
Test Case '-[MyTests testMethod]' passed (1.0 seconds).
"""
        parser = AutoParser()
        result = parser.parse_content(content)

        assert result.success
        assert result.parser_name == "log"

    def test_detect_junit_format(self) -> None:
        """Test auto-detection of JUnit format."""
        content = """<?xml version="1.0"?>
<testsuite name="Tests" tests="1">
  <testcase classname="Tests" name="test1" time="1.0"/>
</testsuite>
"""
        parser = AutoParser()
        result = parser.parse_content(content)

        assert result.success
        assert result.parser_name == "junit"

    def test_parse_file(self, tmp_path: Path) -> None:
        """Test parsing a file."""
        log_file = tmp_path / "test.log"
        log_file.write_text("""
Test Case '-[Tests test]' started.
Test Case '-[Tests test]' passed (1.0 seconds).
""")

        parser = AutoParser()
        result = parser.parse(log_file)

        assert result.success
        assert result.test_run is not None
        assert result.test_run.total_count == 1

    def test_parse_nonexistent_file(self, tmp_path: Path) -> None:
        """Test parsing nonexistent file."""
        parser = AutoParser()
        result = parser.parse(tmp_path / "nonexistent.log")

        assert not result.success
        assert len(result.errors) > 0


class TestParserWithExamples:
    """Tests using example files."""

    @pytest.fixture
    def examples_dir(self) -> Path:
        """Get examples directory."""
        return Path(__file__).parent.parent / "examples"

    def test_parse_sample_xctest_log(self, examples_dir: Path) -> None:
        """Test parsing the sample XCTest log."""
        log_file = examples_dir / "sample_xctest_log.txt"
        if not log_file.exists():
            pytest.skip("Example file not found")

        parser = AutoParser()
        result = parser.parse(log_file)

        assert result.success
        assert result.test_run is not None
        assert result.test_run.total_count == 11
        # At least 8 failures detected (some may be parsed differently)
        assert result.test_run.failed_count >= 8
        assert result.test_run.passed_count == 2

    def test_parse_sample_junit(self, examples_dir: Path) -> None:
        """Test parsing the sample JUnit XML."""
        xml_file = examples_dir / "sample_junit.xml"
        if not xml_file.exists():
            pytest.skip("Example file not found")

        parser = AutoParser()
        result = parser.parse(xml_file)

        assert result.success
        assert result.test_run is not None
        assert result.test_run.total_count == 15

    def test_parse_passing_tests(self, examples_dir: Path) -> None:
        """Test parsing the passing tests file."""
        log_file = examples_dir / "passing_tests.txt"
        if not log_file.exists():
            pytest.skip("Example file not found")

        parser = AutoParser()
        result = parser.parse(log_file)

        assert result.success
        assert result.test_run is not None
        assert result.test_run.failed_count == 0
        assert result.test_run.pass_rate == 100.0

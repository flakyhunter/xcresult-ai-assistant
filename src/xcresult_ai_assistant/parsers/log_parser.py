"""Parser for XCTest log files and console output."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from xcresult_ai_assistant.models.test_result import TestResult, TestRun, TestStatus, TestSuite
from xcresult_ai_assistant.parsers.base import BaseParser, ParserResult


class LogParser(BaseParser):
    """Parser for XCTest log files and console output."""

    name = "log"
    supported_extensions = [".txt", ".log", ".xcresult.log"]

    # Patterns for parsing XCTest output
    TEST_START_PATTERN = re.compile(
        r"Test Case '-\[(\w+)\s+(\w+)\]' started\."
    )
    TEST_PASSED_PATTERN = re.compile(
        r"Test Case '-\[(\w+)\s+(\w+)\]' passed \((\d+\.?\d*) seconds\)\."
    )
    TEST_FAILED_PATTERN = re.compile(
        r"Test Case '-\[(\w+)\s+(\w+)\]' failed \((\d+\.?\d*) seconds\)\."
    )
    ASSERTION_FAILURE_PATTERN = re.compile(
        r"([\w/]+\.swift):(\d+):\s*(error|failed|failure):\s*(.+)"
    )
    SUITE_START_PATTERN = re.compile(
        r"Test Suite '(\w+)' started at (.+)"
    )
    SUITE_FINISHED_PATTERN = re.compile(
        r"Test Suite '(\w+)' (passed|failed) at .+ Executed (\d+) tests?, with (\d+) failures?"
    )
    CRASH_PATTERN = re.compile(
        r"(crash|CRASH|Crash|EXC_BAD_ACCESS|SIGABRT|SIGSEGV|Fatal error)"
    )
    TIMEOUT_PATTERN = re.compile(
        r"(timed? ?out|timeout|exceeded time limit|wait.*expired|deadline)"
    )
    ELEMENT_NOT_FOUND_PATTERN = re.compile(
        r"(No matches found|element.*not found|unable to find|doesn't exist|failed to find)"
    )

    def can_parse(self, path: Path) -> bool:
        """Check if this parser can handle the file."""
        if path.is_file():
            suffix = path.suffix.lower()
            if suffix in [".txt", ".log"]:
                return True
            # Check content for XCTest patterns
            try:
                content = path.read_text(errors="replace")[:2000]
                return "Test Case" in content or "Test Suite" in content
            except Exception:
                return False
        return False

    def parse(self, path: Path) -> ParserResult:
        """Parse log file and extract test results."""
        self.errors = []
        self.warnings = []

        if not path.exists():
            self.add_error(f"File not found: {path}")
            return self._create_result(success=False, source_path=str(path))

        try:
            content = path.read_text(errors="replace")
            return self._parse_content(content, str(path))
        except Exception as e:
            self.add_error(f"Failed to read file: {e}")
            return self._create_result(success=False, source_path=str(path))

    def parse_content(self, content: str, source_name: str = "input") -> ParserResult:
        """Parse log content directly."""
        self.errors = []
        self.warnings = []
        return self._parse_content(content, source_name)

    def _parse_content(self, content: str, source_path: str) -> ParserResult:
        """Internal parse implementation."""
        lines = content.splitlines()
        suites: dict[str, TestSuite] = {}
        current_suite_name = "Default"
        current_test: dict[str, Any] | None = None
        tests: list[TestResult] = []
        failure_buffer: list[str] = []
        raw_data: dict[str, Any] = {"lines": len(lines), "patterns_matched": []}

        for i, line in enumerate(lines):
            # Check for suite start
            suite_match = self.SUITE_START_PATTERN.search(line)
            if suite_match:
                current_suite_name = suite_match.group(1)
                if current_suite_name not in suites:
                    suites[current_suite_name] = TestSuite(name=current_suite_name)
                continue

            # Check for test start
            start_match = self.TEST_START_PATTERN.search(line)
            if start_match:
                if current_test:
                    # Save previous incomplete test
                    tests.append(self._finalize_test(current_test, failure_buffer))
                    failure_buffer = []

                current_test = {
                    "class_name": start_match.group(1),
                    "name": start_match.group(2),
                    "suite_name": current_suite_name,
                    "status": TestStatus.FAILED,  # Default to failed until we see passed
                    "duration": 0.0,
                    "message": "",
                    "stack_trace": "",
                    "raw_output": line,
                }
                raw_data["patterns_matched"].append("test_start")
                continue

            # Check for test passed
            passed_match = self.TEST_PASSED_PATTERN.search(line)
            if passed_match:
                class_name = passed_match.group(1)
                test_name = passed_match.group(2)
                duration = float(passed_match.group(3))

                if current_test and current_test["name"] == test_name:
                    current_test["status"] = TestStatus.PASSED
                    current_test["duration"] = duration
                    tests.append(self._finalize_test(current_test, failure_buffer))
                else:
                    # Test without start marker
                    tests.append(TestResult(
                        name=test_name,
                        class_name=class_name,
                        suite_name=current_suite_name,
                        status=TestStatus.PASSED,
                        duration=duration,
                    ))
                current_test = None
                failure_buffer = []
                raw_data["patterns_matched"].append("test_passed")
                continue

            # Check for test failed
            failed_match = self.TEST_FAILED_PATTERN.search(line)
            if failed_match:
                class_name = failed_match.group(1)
                test_name = failed_match.group(2)
                duration = float(failed_match.group(3))

                if current_test and current_test["name"] == test_name:
                    current_test["status"] = TestStatus.FAILED
                    current_test["duration"] = duration
                    tests.append(self._finalize_test(current_test, failure_buffer))
                else:
                    tests.append(TestResult(
                        name=test_name,
                        class_name=class_name,
                        suite_name=current_suite_name,
                        status=TestStatus.FAILED,
                        duration=duration,
                        message="\n".join(failure_buffer),
                    ))
                current_test = None
                failure_buffer = []
                raw_data["patterns_matched"].append("test_failed")
                continue

            # Check for assertion failures
            assertion_match = self.ASSERTION_FAILURE_PATTERN.search(line)
            if assertion_match:
                file_path = assertion_match.group(1)
                line_num = int(assertion_match.group(2))
                message = assertion_match.group(4)

                if current_test:
                    current_test["file_path"] = file_path
                    current_test["line_number"] = line_num
                    if not current_test["message"]:
                        current_test["message"] = message
                failure_buffer.append(line)
                raw_data["patterns_matched"].append("assertion_failure")
                continue

            # Collect failure info for current test
            if current_test:
                if (self.CRASH_PATTERN.search(line) or
                    self.TIMEOUT_PATTERN.search(line) or
                    self.ELEMENT_NOT_FOUND_PATTERN.search(line) or
                    "error:" in line.lower() or
                    "failed" in line.lower()):
                    failure_buffer.append(line)

        # Finalize last test if incomplete
        if current_test:
            tests.append(self._finalize_test(current_test, failure_buffer))

        # Group tests into suites
        for test in tests:
            suite_name = test.suite_name or "Default"
            if suite_name not in suites:
                suites[suite_name] = TestSuite(name=suite_name)
            suites[suite_name].tests.append(test)

        # Create test run
        test_run = TestRun(
            name=Path(source_path).stem,
            suites=list(suites.values()),
            source_path=source_path,
        )

        # Calculate durations
        for suite in test_run.suites:
            suite.duration = sum(t.duration for t in suite.tests)

        raw_data["total_tests"] = len(tests)
        raw_data["total_suites"] = len(suites)

        return self._create_result(
            test_run=test_run,
            success=True,
            raw_data=raw_data,
            source_path=source_path,
        )

    def _finalize_test(
        self,
        test_data: dict[str, Any],
        failure_buffer: list[str],
    ) -> TestResult:
        """Create TestResult from accumulated data."""
        stack_trace = "\n".join(failure_buffer) if failure_buffer else ""

        # Detect special failure types
        status = test_data.get("status", TestStatus.FAILED)
        if failure_buffer:
            combined = "\n".join(failure_buffer)
            if self.CRASH_PATTERN.search(combined):
                status = TestStatus.CRASHED
            elif self.TIMEOUT_PATTERN.search(combined):
                status = TestStatus.TIMEOUT

        return TestResult(
            name=test_data.get("name", "unknown"),
            class_name=test_data.get("class_name", ""),
            suite_name=test_data.get("suite_name", ""),
            status=status,
            duration=test_data.get("duration", 0.0),
            message=test_data.get("message", ""),
            stack_trace=stack_trace,
            file_path=test_data.get("file_path", ""),
            line_number=test_data.get("line_number", 0),
            raw_output=test_data.get("raw_output", ""),
        )

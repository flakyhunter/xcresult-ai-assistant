"""Parser for JUnit XML format."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any

from xcresult_ai_assistant.models.test_result import TestResult, TestRun, TestStatus, TestSuite
from xcresult_ai_assistant.parsers.base import BaseParser, ParserResult


class JUnitParser(BaseParser):
    """Parser for JUnit XML format test results."""

    name = "junit"
    supported_extensions = [".xml"]

    def can_parse(self, path: Path) -> bool:
        """Check if this parser can handle the file."""
        if not path.is_file() or path.suffix.lower() != ".xml":
            return False

        try:
            content = path.read_text(errors="replace")[:500]
            return "<testsuite" in content or "<testsuites" in content
        except Exception:
            return False

    def parse(self, path: Path) -> ParserResult:
        """Parse JUnit XML file."""
        self.errors = []
        self.warnings = []

        if not path.exists():
            self.add_error(f"File not found: {path}")
            return self._create_result(success=False, source_path=str(path))

        try:
            tree = ET.parse(path)
            root = tree.getroot()
            return self._parse_xml(root, str(path))
        except ET.ParseError as e:
            self.add_error(f"XML parse error: {e}")
            return self._create_result(success=False, source_path=str(path))
        except Exception as e:
            self.add_error(f"Parse error: {e}")
            return self._create_result(success=False, source_path=str(path))

    def parse_content(self, content: str, source_name: str = "input") -> ParserResult:
        """Parse JUnit XML content directly."""
        self.errors = []
        self.warnings = []

        try:
            root = ET.fromstring(content)
            return self._parse_xml(root, source_name)
        except ET.ParseError as e:
            self.add_error(f"XML parse error: {e}")
            return self._create_result(success=False, source_path=source_name)

    def _parse_xml(self, root: ET.Element, source_path: str) -> ParserResult:
        """Parse XML element tree."""
        suites: list[TestSuite] = []
        raw_data: dict[str, Any] = {"format": "junit"}

        # Handle both <testsuites> wrapper and direct <testsuite>
        if root.tag == "testsuites":
            for suite_elem in root.findall("testsuite"):
                suite = self._parse_suite(suite_elem)
                if suite:
                    suites.append(suite)
        elif root.tag == "testsuite":
            suite = self._parse_suite(root)
            if suite:
                suites.append(suite)
        else:
            self.add_error(f"Unknown root element: {root.tag}")
            return self._create_result(success=False, source_path=source_path)

        # Extract run-level attributes
        run_name = root.get("name", Path(source_path).stem)
        timestamp_str = root.get("timestamp", "")
        start_time = None
        if timestamp_str:
            try:
                start_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        test_run = TestRun(
            name=run_name,
            suites=suites,
            start_time=start_time,
            source_path=source_path,
        )

        raw_data["total_tests"] = test_run.total_count
        raw_data["total_suites"] = len(suites)

        return self._create_result(
            test_run=test_run,
            success=True,
            raw_data=raw_data,
            source_path=source_path,
        )

    def _parse_suite(self, suite_elem: ET.Element) -> TestSuite | None:
        """Parse a testsuite element."""
        name = suite_elem.get("name", "Unknown")
        tests: list[TestResult] = []

        # Parse duration
        time_str = suite_elem.get("time", "0")
        try:
            duration = float(time_str)
        except ValueError:
            duration = 0.0

        # Parse timestamp
        timestamp_str = suite_elem.get("timestamp", "")
        timestamp = None
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        # Parse test cases
        for testcase_elem in suite_elem.findall("testcase"):
            test = self._parse_testcase(testcase_elem, name)
            tests.append(test)

        return TestSuite(
            name=name,
            tests=tests,
            duration=duration,
            timestamp=timestamp,
        )

    def _parse_testcase(self, testcase_elem: ET.Element, suite_name: str) -> TestResult:
        """Parse a testcase element."""
        name = testcase_elem.get("name", "unknown")
        class_name = testcase_elem.get("classname", "")

        # Parse duration
        time_str = testcase_elem.get("time", "0")
        try:
            duration = float(time_str)
        except ValueError:
            duration = 0.0

        # Determine status and extract failure info
        status = TestStatus.PASSED
        message = ""
        stack_trace = ""

        # Check for failure
        failure_elem = testcase_elem.find("failure")
        if failure_elem is not None:
            status = TestStatus.FAILED
            message = failure_elem.get("message", "")
            stack_trace = failure_elem.text or ""

        # Check for error
        error_elem = testcase_elem.find("error")
        if error_elem is not None:
            status = TestStatus.ERROR
            message = error_elem.get("message", "")
            stack_trace = error_elem.text or ""

        # Check for skipped
        skipped_elem = testcase_elem.find("skipped")
        if skipped_elem is not None:
            status = TestStatus.SKIPPED
            message = skipped_elem.get("message", "Skipped")

        # Check for system-out/system-err
        raw_output = ""
        stdout_elem = testcase_elem.find("system-out")
        if stdout_elem is not None and stdout_elem.text:
            raw_output = stdout_elem.text

        stderr_elem = testcase_elem.find("system-err")
        if stderr_elem is not None and stderr_elem.text:
            if raw_output:
                raw_output += "\n---STDERR---\n"
            raw_output += stderr_elem.text

        return TestResult(
            name=name,
            class_name=class_name,
            suite_name=suite_name,
            status=status,
            duration=duration,
            message=message,
            stack_trace=stack_trace,
            raw_output=raw_output,
        )

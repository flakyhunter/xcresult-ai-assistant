"""Parser for .xcresult bundles."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from xcresult_ai_assistant.models.test_result import TestResult, TestRun, TestStatus, TestSuite
from xcresult_ai_assistant.parsers.base import BaseParser, ParserResult


class XCResultParser(BaseParser):
    """Parser for .xcresult bundles using xcresulttool."""

    name = "xcresult"
    supported_extensions = [".xcresult"]

    def __init__(self, verbose: bool = False):
        """Initialize parser."""
        super().__init__(verbose)
        self._xcresulttool_available: bool | None = None

    @property
    def xcresulttool_available(self) -> bool:
        """Check if xcresulttool is available."""
        if self._xcresulttool_available is None:
            try:
                result = subprocess.run(
                    ["xcrun", "xcresulttool", "version"],
                    capture_output=True,
                    timeout=5,
                )
                self._xcresulttool_available = result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                self._xcresulttool_available = False
        return self._xcresulttool_available

    def can_parse(self, path: Path) -> bool:
        """Check if this parser can handle the path."""
        return path.is_dir() and path.suffix == ".xcresult"

    def parse(self, path: Path) -> ParserResult:
        """Parse xcresult bundle."""
        self.errors = []
        self.warnings = []

        if not path.exists():
            self.add_error(f"Path not found: {path}")
            return self._create_result(success=False, source_path=str(path))

        if not path.is_dir():
            self.add_error(f"Not a directory: {path}")
            return self._create_result(success=False, source_path=str(path))

        if not path.suffix == ".xcresult":
            self.add_error(f"Not an xcresult bundle: {path}")
            return self._create_result(success=False, source_path=str(path))

        if self.xcresulttool_available:
            return self._parse_with_xcresulttool(path)
        else:
            self.add_warning("xcresulttool not available, using fallback parser")
            return self._parse_fallback(path)

    def _parse_with_xcresulttool(self, path: Path) -> ParserResult:
        """Parse using xcresulttool."""
        try:
            # Get root object
            result = subprocess.run(
                ["xcrun", "xcresulttool", "get", "--path", str(path), "--format", "json"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                self.add_error(f"xcresulttool failed: {result.stderr}")
                return self._parse_fallback(path)

            root_data = json.loads(result.stdout)
            return self._process_xcresult_data(root_data, path)

        except subprocess.TimeoutExpired:
            self.add_error("xcresulttool timed out")
            return self._parse_fallback(path)
        except json.JSONDecodeError as e:
            self.add_error(f"Failed to parse xcresulttool output: {e}")
            return self._parse_fallback(path)
        except Exception as e:
            self.add_error(f"xcresulttool error: {e}")
            return self._parse_fallback(path)

    def _process_xcresult_data(self, data: dict[str, Any], path: Path) -> ParserResult:
        """Process xcresulttool JSON output."""
        tests: list[TestResult] = []
        suites: dict[str, TestSuite] = {}
        raw_data: dict[str, Any] = {"xcresult_format": True}

        # Extract metadata
        metrics = data.get("metrics", {})
        run_destination = data.get("runDestination", {})

        # Extract test results from actions
        actions = data.get("actions", {}).get("_values", [])
        for action in actions:
            action_result = action.get("actionResult", {})
            tests_ref = action_result.get("testsRef", {})

            if tests_ref.get("id", {}).get("_value"):
                # Need to get the actual test data
                test_data = self._get_test_reference(path, tests_ref["id"]["_value"])
                if test_data:
                    self._extract_tests_from_data(test_data, tests, suites)

        # If no tests found via references, try direct extraction
        if not tests:
            self._extract_tests_directly(data, tests, suites)

        # Create test run
        device_name = run_destination.get("displayName", {}).get("_value", "")
        os_version = run_destination.get("targetSDKRecord", {}).get("operatingSystemVersion", {}).get("_value", "")

        test_run = TestRun(
            name=path.stem,
            suites=list(suites.values()) if suites else [TestSuite(name="Default", tests=tests)],
            device=device_name,
            os_version=os_version,
            source_path=str(path),
        )

        raw_data["total_tests"] = len(tests)
        raw_data["total_suites"] = len(suites)

        return self._create_result(
            test_run=test_run,
            success=True,
            raw_data=raw_data,
            source_path=str(path),
        )

    def _get_test_reference(self, path: Path, ref_id: str) -> dict[str, Any] | None:
        """Get test data from reference ID."""
        try:
            result = subprocess.run(
                ["xcrun", "xcresulttool", "get", "--path", str(path),
                 "--format", "json", "--id", ref_id],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception:
            pass
        return None

    def _extract_tests_from_data(
        self,
        data: dict[str, Any],
        tests: list[TestResult],
        suites: dict[str, TestSuite],
    ) -> None:
        """Extract test results from xcresult data structure."""
        summaries = data.get("summaries", {}).get("_values", [])
        for summary in summaries:
            testableSummaries = summary.get("testableSummaries", {}).get("_values", [])
            for testable in testableSummaries:
                self._process_testable(testable, tests, suites)

    def _process_testable(
        self,
        testable: dict[str, Any],
        tests: list[TestResult],
        suites: dict[str, TestSuite],
    ) -> None:
        """Process a testable summary."""
        testable_tests = testable.get("tests", {}).get("_values", [])
        for test_group in testable_tests:
            self._process_test_group(test_group, tests, suites, "")

    def _process_test_group(
        self,
        group: dict[str, Any],
        tests: list[TestResult],
        suites: dict[str, TestSuite],
        parent_name: str,
    ) -> None:
        """Recursively process test groups."""
        name = group.get("name", {}).get("_value", "")
        full_name = f"{parent_name}.{name}" if parent_name else name

        # Check if this is a test case or a group
        subtests = group.get("subtests", {}).get("_values", [])

        if subtests:
            # This is a group, recurse
            for subtest in subtests:
                self._process_test_group(subtest, tests, suites, full_name)
        else:
            # This is a test case
            status_str = group.get("testStatus", {}).get("_value", "")
            duration = group.get("duration", {}).get("_value", 0.0)

            status = self._map_status(status_str)
            message = ""
            stack_trace = ""

            # Extract failure info
            failure_summaries = group.get("failureSummaries", {}).get("_values", [])
            if failure_summaries:
                messages = []
                traces = []
                for failure in failure_summaries:
                    msg = failure.get("message", {}).get("_value", "")
                    if msg:
                        messages.append(msg)
                    loc = failure.get("sourceCodeContext", {}).get("location", {})
                    if loc:
                        file_path = loc.get("filePath", {}).get("_value", "")
                        line_num = loc.get("lineNumber", {}).get("_value", 0)
                        traces.append(f"{file_path}:{line_num}")
                message = "\n".join(messages)
                stack_trace = "\n".join(traces)

            # Determine suite and test name
            parts = full_name.rsplit(".", 1)
            if len(parts) == 2:
                suite_name, test_name = parts
            else:
                suite_name = "Default"
                test_name = full_name

            test_result = TestResult(
                name=test_name,
                class_name=suite_name.split(".")[-1] if "." in suite_name else suite_name,
                suite_name=suite_name,
                status=status,
                duration=float(duration) if isinstance(duration, (int, float, str)) else 0.0,
                message=message,
                stack_trace=stack_trace,
            )

            tests.append(test_result)

            if suite_name not in suites:
                suites[suite_name] = TestSuite(name=suite_name)
            suites[suite_name].tests.append(test_result)

    def _extract_tests_directly(
        self,
        data: dict[str, Any],
        tests: list[TestResult],
        suites: dict[str, TestSuite],
    ) -> None:
        """Extract tests directly from root data when references fail."""
        # Try to find test counts at least
        metrics = data.get("metrics", {})
        test_count = metrics.get("testsCount", {}).get("_value", 0)
        failed_count = metrics.get("testsFailedCount", {}).get("_value", 0)

        if test_count > 0 and not tests:
            # Create placeholder results based on metrics
            passed_count = test_count - failed_count
            for i in range(passed_count):
                tests.append(TestResult(
                    name=f"test_{i+1}",
                    status=TestStatus.PASSED,
                ))
            for i in range(failed_count):
                tests.append(TestResult(
                    name=f"failed_test_{i+1}",
                    status=TestStatus.FAILED,
                    message="Details unavailable - check xcresult bundle",
                ))

            self.add_warning(f"Created {test_count} placeholder test results from metrics")

    def _map_status(self, status_str: str) -> TestStatus:
        """Map xcresult status string to TestStatus."""
        status_map = {
            "Success": TestStatus.PASSED,
            "Failure": TestStatus.FAILED,
            "Expected Failure": TestStatus.FAILED,
            "Skipped": TestStatus.SKIPPED,
        }
        return status_map.get(status_str, TestStatus.FAILED)

    def _parse_fallback(self, path: Path) -> ParserResult:
        """Fallback parsing when xcresulttool is unavailable."""
        tests: list[TestResult] = []
        raw_data: dict[str, Any] = {"fallback_mode": True}

        # Look for any readable files in the bundle
        for file_path in path.rglob("*"):
            if file_path.is_file() and file_path.suffix in [".txt", ".log"]:
                try:
                    content = file_path.read_text(errors="replace")
                    # Look for test patterns
                    if "Test Case" in content:
                        from xcresult_ai_assistant.parsers.log_parser import LogParser
                        log_parser = LogParser(verbose=self.verbose)
                        log_result = log_parser.parse_content(content, str(file_path))
                        if log_result.test_run:
                            tests.extend(log_result.test_run.all_tests)
                except Exception:
                    continue

        if not tests:
            self.add_warning("No test data extracted from xcresult bundle")
            # Create minimal result
            test_run = TestRun(
                name=path.stem,
                source_path=str(path),
            )
        else:
            test_run = TestRun(
                name=path.stem,
                suites=[TestSuite(name="Extracted", tests=tests)],
                source_path=str(path),
            )

        raw_data["total_tests"] = len(tests)

        return self._create_result(
            test_run=test_run,
            success=True,
            raw_data=raw_data,
            source_path=str(path),
        )

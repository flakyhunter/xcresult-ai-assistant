"""Test result data models."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TestStatus(str, Enum):
    """Status of a test execution."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    TIMEOUT = "timeout"
    CRASHED = "crashed"


class TestResult(BaseModel):
    """Individual test result."""

    name: str = Field(..., description="Test method name")
    class_name: str = Field(default="", description="Test class name")
    suite_name: str = Field(default="", description="Test suite name")
    status: TestStatus = Field(..., description="Test execution status")
    duration: float = Field(default=0.0, description="Test duration in seconds")
    message: str = Field(default="", description="Failure message if failed")
    stack_trace: str = Field(default="", description="Stack trace if available")
    file_path: str = Field(default="", description="Source file path")
    line_number: int = Field(default=0, description="Line number of failure")
    attachments: list[str] = Field(default_factory=list, description="Screenshot/attachment paths")
    raw_output: str = Field(default="", description="Raw test output")
    timestamp: datetime | None = Field(default=None, description="When test was executed")
    retry_count: int = Field(default=0, description="Number of retries attempted")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @property
    def full_name(self) -> str:
        """Get fully qualified test name."""
        parts = []
        if self.suite_name:
            parts.append(self.suite_name)
        if self.class_name:
            parts.append(self.class_name)
        parts.append(self.name)
        return ".".join(parts)

    @property
    def is_failure(self) -> bool:
        """Check if test is a failure."""
        return self.status in (TestStatus.FAILED, TestStatus.ERROR, TestStatus.CRASHED)

    @property
    def location(self) -> str:
        """Get file location string."""
        if self.file_path and self.line_number:
            return f"{self.file_path}:{self.line_number}"
        return self.file_path or "unknown"


class TestSuite(BaseModel):
    """Collection of test results from a single suite."""

    name: str = Field(..., description="Suite name")
    tests: list[TestResult] = Field(default_factory=list, description="Test results")
    duration: float = Field(default=0.0, description="Total suite duration")
    timestamp: datetime | None = Field(default=None, description="Suite execution time")

    @property
    def total_count(self) -> int:
        """Total number of tests."""
        return len(self.tests)

    @property
    def passed_count(self) -> int:
        """Number of passed tests."""
        return sum(1 for t in self.tests if t.status == TestStatus.PASSED)

    @property
    def failed_count(self) -> int:
        """Number of failed tests."""
        return sum(1 for t in self.tests if t.is_failure)

    @property
    def skipped_count(self) -> int:
        """Number of skipped tests."""
        return sum(1 for t in self.tests if t.status == TestStatus.SKIPPED)

    @property
    def pass_rate(self) -> float:
        """Pass rate as percentage."""
        if self.total_count == 0:
            return 0.0
        return (self.passed_count / self.total_count) * 100


class TestRun(BaseModel):
    """Complete test run containing multiple suites."""

    name: str = Field(default="Test Run", description="Run name/identifier")
    suites: list[TestSuite] = Field(default_factory=list, description="Test suites")
    start_time: datetime | None = Field(default=None, description="Run start time")
    end_time: datetime | None = Field(default=None, description="Run end time")
    device: str = Field(default="", description="Device/simulator name")
    os_version: str = Field(default="", description="OS version")
    xcode_version: str = Field(default="", description="Xcode version")
    configuration: str = Field(default="", description="Build configuration")
    source_path: str = Field(default="", description="Source file/bundle path")

    @property
    def all_tests(self) -> list[TestResult]:
        """Get all tests across all suites."""
        tests = []
        for suite in self.suites:
            tests.extend(suite.tests)
        return tests

    @property
    def failed_tests(self) -> list[TestResult]:
        """Get all failed tests."""
        return [t for t in self.all_tests if t.is_failure]

    @property
    def total_count(self) -> int:
        """Total test count."""
        return sum(s.total_count for s in self.suites)

    @property
    def passed_count(self) -> int:
        """Total passed count."""
        return sum(s.passed_count for s in self.suites)

    @property
    def failed_count(self) -> int:
        """Total failed count."""
        return sum(s.failed_count for s in self.suites)

    @property
    def duration(self) -> timedelta:
        """Total run duration."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return timedelta(seconds=sum(s.duration for s in self.suites))

    @property
    def pass_rate(self) -> float:
        """Overall pass rate."""
        if self.total_count == 0:
            return 0.0
        return (self.passed_count / self.total_count) * 100

"""Base parser interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from xcresult_ai_assistant.models.test_result import TestRun


class ParserResult(BaseModel):
    """Result of parsing operation."""

    success: bool = Field(default=True, description="Parse succeeded")
    test_run: TestRun | None = Field(default=None, description="Parsed test run")
    errors: list[str] = Field(default_factory=list, description="Parse errors")
    warnings: list[str] = Field(default_factory=list, description="Parse warnings")
    raw_data: dict[str, Any] = Field(default_factory=dict, description="Raw parsed data")
    source_path: str = Field(default="", description="Source file path")
    parser_name: str = Field(default="", description="Parser used")


class BaseParser(ABC):
    """Base class for all parsers."""

    name: str = "base"
    supported_extensions: list[str] = []

    def __init__(self, verbose: bool = False):
        """Initialize parser."""
        self.verbose = verbose
        self.errors: list[str] = []
        self.warnings: list[str] = []

    @abstractmethod
    def can_parse(self, path: Path) -> bool:
        """Check if parser can handle the given path."""
        pass

    @abstractmethod
    def parse(self, path: Path) -> ParserResult:
        """Parse the file/directory and return test run."""
        pass

    def parse_content(self, content: str, source_name: str = "input") -> ParserResult:
        """Parse content string directly."""
        # Default implementation - subclasses can override
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            result = self.parse(temp_path)
            result.source_path = source_name
            return result
        finally:
            temp_path.unlink(missing_ok=True)

    def add_error(self, message: str) -> None:
        """Add parse error."""
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        """Add parse warning."""
        self.warnings.append(message)

    def _create_result(
        self,
        test_run: TestRun | None = None,
        success: bool = True,
        raw_data: dict[str, Any] | None = None,
        source_path: str = "",
    ) -> ParserResult:
        """Create parser result with current errors/warnings."""
        return ParserResult(
            success=success and test_run is not None,
            test_run=test_run,
            errors=self.errors.copy(),
            warnings=self.warnings.copy(),
            raw_data=raw_data or {},
            source_path=source_path,
            parser_name=self.name,
        )

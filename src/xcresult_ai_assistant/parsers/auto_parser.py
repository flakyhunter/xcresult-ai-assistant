"""Auto-detecting parser that selects the appropriate parser."""

from __future__ import annotations

from pathlib import Path

from xcresult_ai_assistant.parsers.base import BaseParser, ParserResult
from xcresult_ai_assistant.parsers.junit_parser import JUnitParser
from xcresult_ai_assistant.parsers.log_parser import LogParser
from xcresult_ai_assistant.parsers.xcresult_parser import XCResultParser


class AutoParser(BaseParser):
    """Parser that automatically detects and uses the appropriate parser."""

    name = "auto"
    supported_extensions = [".xcresult", ".xml", ".txt", ".log"]

    def __init__(self, verbose: bool = False):
        """Initialize auto parser with all sub-parsers."""
        super().__init__(verbose)
        self.parsers: list[BaseParser] = [
            XCResultParser(verbose=verbose),
            JUnitParser(verbose=verbose),
            LogParser(verbose=verbose),
        ]

    def can_parse(self, path: Path) -> bool:
        """Check if any parser can handle the path."""
        return any(p.can_parse(path) for p in self.parsers)

    def parse(self, path: Path) -> ParserResult:
        """Auto-detect format and parse."""
        self.errors = []
        self.warnings = []

        if not path.exists():
            self.add_error(f"Path not found: {path}")
            return self._create_result(success=False, source_path=str(path))

        # Try each parser in order
        for parser in self.parsers:
            if parser.can_parse(path):
                if self.verbose:
                    self.add_warning(f"Using {parser.name} parser")
                result = parser.parse(path)
                # Copy warnings/errors
                self.errors.extend(parser.errors)
                self.warnings.extend(parser.warnings)
                return result

        # No parser found
        self.add_error(f"No suitable parser found for: {path}")
        return self._create_result(success=False, source_path=str(path))

    def parse_content(self, content: str, source_name: str = "input") -> ParserResult:
        """Auto-detect format and parse content."""
        self.errors = []
        self.warnings = []

        # Try to detect format from content
        content_lower = content[:1000].lower()

        # Check for XML/JUnit
        if content.strip().startswith("<?xml") or "<testsuite" in content_lower:
            parser = JUnitParser(verbose=self.verbose)
            if self.verbose:
                self.add_warning("Detected JUnit XML format")
        # Check for XCTest log patterns
        elif "test case" in content_lower or "test suite" in content_lower:
            parser = LogParser(verbose=self.verbose)
            if self.verbose:
                self.add_warning("Detected XCTest log format")
        else:
            # Default to log parser
            parser = LogParser(verbose=self.verbose)
            if self.verbose:
                self.add_warning("Using default log parser")

        result = parser.parse_content(content, source_name)
        self.errors.extend(parser.errors)
        self.warnings.extend(parser.warnings)
        return result

    def get_parser_for_path(self, path: Path) -> BaseParser | None:
        """Get the parser that would be used for a path."""
        for parser in self.parsers:
            if parser.can_parse(path):
                return parser
        return None

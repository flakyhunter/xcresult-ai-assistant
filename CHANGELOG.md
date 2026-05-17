# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-05-17

### Added

- **Xcode 17+ support**: Updated XCTest log parser to handle new test output format
  - Support for `Module.ClassName` format in test case markers
  - Support for `(Iteration X of Y)` suffix in test names
  - Enhanced error message parsing with module prefix support
- **xcresulttool `--legacy` flag**: Added fallback to legacy mode for Xcode 17+ compatibility
- **Improved fallback parsing**: Priority file patterns for `StandardOutputAndStandardError.txt` in xcresult bundles
- **New failure patterns**:
  - `did NOT exist` patterns for missing UI elements
  - `within X.Xs` patterns for timeout detection
  - `StaticText/Button/TextField did NOT exist` specific patterns

### Fixed

- **TIMEOUT status not counted as failure**: Tests with `TestStatus.TIMEOUT` were incorrectly excluded from failure analysis. Now properly included in `is_failure` property
- **Pattern analyzer regex**: Fixed patterns to match B2Core-style error messages

### Changed

- Enhanced `ASSERTION_FAILURE_PATTERN` to handle `-[Module.Class method]` prefix in error messages
- Improved `TIMEOUT_PATTERN` with more comprehensive matching
- Improved `ELEMENT_NOT_FOUND_PATTERN` with XCTest-specific error formats

## [0.1.0] - 2024-05-17

### Added

- Initial release of xcresult-ai-assistant
- **Multi-format parsing**: XCTest logs, JUnit XML, xcresult bundles
- **30+ failure categories**: Timeouts, crashes, missing elements, network errors, race conditions, and more
- **AI-style root cause analysis**: Intelligent failure explanation with confidence scores
- **Flaky test detection**: Identifies tests likely to be flaky with scoring algorithm
- **Smart debugging suggestions**: Context-aware recommendations with Swift code examples
- **Multiple output formats**: Console, Markdown, JSON, HTML
- **Priority-based triage**: Ranks failures by severity and actionability
- **CLI commands**:
  - `analyze` - Analyze test results with rich output
  - `explain` - AI-powered failure explanation with root cause analysis
  - `flaky` - Detect flaky tests
  - `categories` - Show failure category breakdown
  - `summarize` - Summarize multiple test result files
  - `info` - Show tool capabilities
- **CI/CD workflows**:
  - GitHub Actions CI for Python 3.9-3.13 on Ubuntu and macOS
  - Release workflow with automatic GitHub Release creation
- Comprehensive test suite (106+ tests)
- Full documentation in README

### Technical

- Built with Python 3.9+ support
- Uses Typer for CLI, Rich for terminal output, Pydantic for data models
- Pattern-based failure categorization with 40+ regex patterns
- Extensible reporter architecture for adding new output formats

[0.2.0]: https://github.com/flakyhunter/xcresult-ai-assistant/releases/tag/v0.2.0
[0.1.0]: https://github.com/flakyhunter/xcresult-ai-assistant/releases/tag/v0.1.0

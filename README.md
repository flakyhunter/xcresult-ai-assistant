# XCResult AI Assistant

[![CI](https://github.com/flakyhunter/xcresult-ai-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/flakyhunter/xcresult-ai-assistant/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

AI-powered assistant for analyzing XCTest failures, xcresult bundles, and test logs. Automatically categorizes failures, detects flaky tests, and provides actionable debugging suggestions with root cause analysis.

## Features

- **Multi-format parsing**: XCTest logs, JUnit XML, xcresult bundles
- **30+ failure categories**: Timeouts, crashes, missing elements, network errors, race conditions, and more
- **AI-style root cause analysis**: Intelligent failure explanation with confidence scores
- **Flaky test detection**: Identifies tests likely to be flaky with scoring
- **Smart debugging suggestions**: Context-aware recommendations with Swift code examples
- **Multiple output formats**: Console, Markdown, JSON, HTML
- **Priority-based triage**: Ranks failures by severity and actionability

## Installation

```bash
# Install from GitHub
pip install git+https://github.com/flakyhunter/xcresult-ai-assistant.git

# Or clone and install locally
git clone https://github.com/flakyhunter/xcresult-ai-assistant.git
cd xcresult-ai-assistant
pip install -e .
```

### Requirements

- Python 3.9+
- macOS (required for xcresult bundle parsing)

## Quick Start

```bash
# Analyze test results
xcresult-ai analyze tests.log

# Get AI-powered failure explanations
xcresult-ai explain tests.log

# Generate HTML report
xcresult-ai analyze tests.log --format html --output report.html

# Detect flaky tests
xcresult-ai flaky tests.log

# View failure categories
xcresult-ai categories tests.log
```

## CLI Commands

### `analyze` - Analyze test results

```bash
xcresult-ai analyze <path> [options]

Options:
  --format, -f         Output format: console, markdown, json, html (default: console)
  --output, -o         Output file path
  --verbose, -V        Enable verbose output
  --suggestions        Include debugging suggestions (default: true)
  --no-suggestions     Disable debugging suggestions
  --stack-traces       Include full stack traces
  --max-failures, -m   Maximum failures to show (default: 50)
  --group-by-category  Group failures by category (default: true)

Examples:
  xcresult-ai analyze results.xcresult
  xcresult-ai analyze test-output.log --format markdown -o report.md
  xcresult-ai analyze results.xcresult --format html -o report.html
```

### `explain` - AI-powered failure analysis

Deep analysis of failures with root cause identification, confidence scores, and fix suggestions.

```bash
xcresult-ai explain <path> [options]

Options:
  --test, -t     Specific test name to explain (partial match)
  --top, -n      Number of top failures to explain (default: 3)

Examples:
  xcresult-ai explain tests.log
  xcresult-ai explain results.xcresult --test testLogin
  xcresult-ai explain tests.log --top 5
```

**Sample output:**
```
🔍 AI-Powered Failure Analysis

╭─ 1. AuthTests.testLogin ─────────────────────────────────────────╮
│ Severity: MEDIUM                                                  │
│ Category: timeout                                                 │
│ Confidence: 85%                                                   │
│ Flaky Score: 0.45                                                 │
│                                                                   │
│ Error Message:                                                    │
│ Timed out waiting for login button to appear                      │
│                                                                   │
│ 🎯 Likely Root Cause:                                             │
│ Operation exceeded the timeout limit. Common causes:              │
│   • Network request slower than expected                          │
│   • UI animation blocking the test                                │
│   • Background loading not completing                             │
│                                                                   │
│ 💡 Recommended Actions:                                           │
│   1. Increase timeout duration                                    │
│      → Set explicit timeout for slow operations                   │
│   2. Add explicit waits                                           │
│      → Wait for specific element states                           │
╰──────────────────────────────────────────────────────────────────╯
```

### `flaky` - Detect flaky tests

```bash
xcresult-ai flaky <path>
```

### `categories` - Show failure breakdown

```bash
xcresult-ai categories <path>
```

### `summarize` - Summarize multiple test files

```bash
xcresult-ai summarize <directory>
```

### `info` - Show tool capabilities

```bash
xcresult-ai info
```

## Supported Input Formats

### XCTest Logs (.log, .txt)

```
Test Suite 'MyTests' started at 2024-01-15 10:00:00.000
Test Case '-[MyTests testLogin]' started.
Test Case '-[MyTests testLogin]' passed (1.500 seconds).
Test Case '-[MyTests testFailure]' started.
/path/to/file.swift:42: error: -[MyTests testFailure] : XCTAssertEqual failed
Test Case '-[MyTests testFailure]' failed (2.000 seconds).
```

### JUnit XML (.xml)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="MyTests" tests="10" failures="2" time="30.5">
  <testcase classname="MyTests" name="testSuccess" time="1.5"/>
  <testcase classname="MyTests" name="testFailure" time="2.0">
    <failure message="Assertion failed">Expected true but got false</failure>
  </testcase>
</testsuite>
```

### xcresult Bundles (.xcresult)

```bash
xcresult-ai analyze MyTests.xcresult
```

## Failure Categories

| Category | Description |
|----------|-------------|
| `MISSING_ELEMENT` | UI element not found |
| `ELEMENT_NOT_HITTABLE` | Element exists but not tappable |
| `TIMEOUT` | General timeout |
| `WAIT_TIMEOUT` | Explicit wait timeout |
| `APP_CRASH` | Application crashed |
| `ASSERTION_FAILURE` | XCTAssert failed |
| `VALUE_MISMATCH` | Expected vs actual mismatch |
| `NETWORK_ERROR` | Network request failed |
| `RACE_CONDITION` | Timing-dependent failure |
| `SYSTEM_ALERT` | Unexpected system dialog |
| `SNAPSHOT_MISMATCH` | Visual regression detected |
| `KEYBOARD_ISSUE` | Keyboard blocking UI |
| `ACCESSIBILITY_MISSING` | Missing accessibility identifier |
| `SIMULATOR_CRASH` | Simulator crashed |
| `MEMORY_ISSUE` | Memory-related crash |

*...and 15+ more categories*

## Output Formats

### Console (default)
Rich terminal output with colors and formatting.

### Markdown
Perfect for GitHub PRs and documentation.

```bash
xcresult-ai analyze tests.log --format markdown -o report.md
```

### JSON
Machine-readable for CI/CD integration.

```bash
xcresult-ai analyze tests.log --format json -o report.json
```

### HTML
Styled, interactive web report.

```bash
xcresult-ai analyze tests.log --format html -o report.html
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Test Analysis

on: [push, pull_request]

jobs:
  analyze:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run tests
        run: |
          xcodebuild test \
            -scheme MyApp \
            -destination 'platform=iOS Simulator,name=iPhone 15' \
            -resultBundlePath results.xcresult

      - name: Analyze results
        run: |
          pip install git+https://github.com/flakyhunter/xcresult-ai-assistant.git
          xcresult-ai analyze results.xcresult --format html -o report.html
          xcresult-ai analyze results.xcresult --format json -o report.json

      - name: Upload reports
        uses: actions/upload-artifact@v4
        with:
          name: test-analysis
          path: |
            report.html
            report.json
```

## Python API

```python
from xcresult_ai_assistant.parsers.auto_parser import AutoParser
from xcresult_ai_assistant.analyzers.failure_analyzer import FailureAnalyzer
from xcresult_ai_assistant.reports.report_factory import ReportFactory
from xcresult_ai_assistant.models.report import ReportFormat

# Parse test results
parser = AutoParser()
parse_result = parser.parse("tests.log")

# Analyze failures
analyzer = FailureAnalyzer()
analysis = analyzer.analyze(parse_result.test_run)

# Generate reports
markdown_report = ReportFactory.generate_report(analysis, ReportFormat.MARKDOWN)
html_report = ReportFactory.generate_report(analysis, ReportFormat.HTML)

# Save to files
ReportFactory.generate_and_save(analysis, "report.html", ReportFormat.HTML)

# Print summary
print(f"Pass rate: {analysis.pass_rate:.1f}%")
print(f"Flaky tests: {analysis.flaky_count}")
print(f"Top category: {analysis.top_categories[0][0]}")
```

## How It Works

1. **Parsing**: Auto-detects input format and extracts test results
2. **Pattern Matching**: Matches failure messages against 40+ known patterns
3. **Categorization**: Assigns failures to categories with confidence scores
4. **Flaky Detection**: Scores tests for flakiness based on patterns and categories
5. **Root Cause Analysis**: Groups related failures and identifies common causes
6. **Suggestions**: Provides actionable debugging steps with code examples

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=xcresult_ai_assistant --cov-report=html

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

### Project Structure

```
xcresult-ai-assistant/
├── src/xcresult_ai_assistant/
│   ├── models/           # Pydantic data models
│   ├── parsers/          # Input format parsers
│   ├── analyzers/        # Failure analysis engines
│   ├── ai/               # Suggestion engine
│   ├── reports/          # Report generators (console, md, json, html)
│   └── cli.py            # Typer CLI
├── tests/                # Pytest test suite
├── examples/             # Example input files
└── .github/workflows/    # CI/CD workflows
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

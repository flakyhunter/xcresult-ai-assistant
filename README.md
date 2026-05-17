# XCResult AI Assistant

AI-powered assistant for analyzing XCTest failures, xcresult bundles, and test logs. Automatically categorizes failures, detects flaky tests, and provides actionable debugging suggestions.

## Features

- **Multi-format parsing**: XCTest logs, JUnit XML, xcresult bundles
- **Intelligent failure categorization**: 23+ failure categories including timeouts, crashes, missing elements, network errors, race conditions
- **Flaky test detection**: Identifies tests likely to be flaky based on failure patterns
- **AI-style debugging suggestions**: Heuristics-based suggestions with code examples
- **Root cause analysis**: Groups related failures and identifies common causes
- **Multiple output formats**: Console (rich), Markdown, JSON
- **Priority scoring**: Helps triage failures by severity and actionability

## Installation

```bash
# Clone the repository
git clone https://github.com/flakyhunter/xcresult-ai-assistant.git
cd xcresult-ai-assistant

# Install with pip (editable mode for development)
pip install -e .

# Or install dependencies directly
pip install -r requirements.txt
```

### Requirements

- Python 3.9+
- macOS (for xcresult bundle parsing with xcresulttool)

## Quick Start

```bash
# Analyze a test log file
xcresult-ai analyze tests.log

# Analyze with markdown output
xcresult-ai analyze tests.log --format markdown --output report.md

# Analyze with debugging suggestions
xcresult-ai analyze tests.log --suggestions

# Detect flaky tests
xcresult-ai flaky tests.log

# View failure categories
xcresult-ai categories tests.log

# Summarize multiple test files
xcresult-ai summarize ./test-results/
```

## CLI Commands

### `analyze`

Analyze test results and generate a detailed report.

```bash
xcresult-ai analyze <path> [options]

Options:
  --format, -f         Output format: console, markdown, json (default: console)
  --output, -o         Output file path
  --verbose, -V        Enable verbose output
  --suggestions        Include debugging suggestions (default: true)
  --no-suggestions     Disable debugging suggestions
  --stack-traces       Include full stack traces
  --max-failures, -m   Maximum failures to show (default: 50)
  --group-by-category  Group failures by category (default: true)
```

### `flaky`

Detect and analyze potentially flaky tests.

```bash
xcresult-ai flaky <path>
```

### `categories`

Show failure category breakdown.

```bash
xcresult-ai categories <path>
```

### `summarize`

Summarize test results from a directory.

```bash
xcresult-ai summarize <directory>
```

### `info`

Show tool information and available commands.

```bash
xcresult-ai info
```

## Supported Input Formats

### XCTest Logs

Standard Xcode test output format:

```
Test Suite 'MyTests' started at 2024-01-15 10:00:00.000
Test Case '-[MyTests testLogin]' started.
Test Case '-[MyTests testLogin]' passed (1.500 seconds).
Test Case '-[MyTests testFailure]' started.
/path/to/file.swift:42: error: -[MyTests testFailure] : XCTAssertEqual failed
Test Case '-[MyTests testFailure]' failed (2.000 seconds).
```

### JUnit XML

Standard JUnit XML format (also used by many CI systems):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="MyTests" tests="10" failures="2" time="30.5">
  <testcase classname="MyTests" name="testSuccess" time="1.5"/>
  <testcase classname="MyTests" name="testFailure" time="2.0">
    <failure message="Assertion failed">Expected true but got false</failure>
  </testcase>
</testsuite>
```

### xcresult Bundles

Xcode result bundles (requires macOS with Xcode installed):

```bash
xcresult-ai analyze MyTests.xcresult
```

## Failure Categories

The tool recognizes 23 failure categories:

| Category | Description |
|----------|-------------|
| `MISSING_ELEMENT` | UI element not found |
| `TIMEOUT` | General timeout |
| `WAIT_TIMEOUT` | Explicit wait timeout |
| `APP_CRASH` | Application crashed |
| `ASSERTION_FAILURE` | XCTAssert failed |
| `VALUE_MISMATCH` | Expected vs actual mismatch |
| `ELEMENT_NOT_HITTABLE` | Element exists but not tappable |
| `NETWORK_ERROR` | Network request failed |
| `AUTHENTICATION_ERROR` | Auth/login failure |
| `RACE_CONDITION` | Timing-dependent failure |
| `SYSTEM_ALERT` | Unexpected system dialog |
| `KEYBOARD_INTERFERENCE` | Keyboard blocking UI |
| `SNAPSHOT_MISMATCH` | Visual regression detected |
| `ACCESSIBILITY_ISSUE` | A11y-related failure |
| `STATE_ERROR` | Invalid app state |
| `CONFIGURATION_ERROR` | Test setup issue |
| `SIMULATOR_CRASH` | Simulator crashed |
| `INFRASTRUCTURE_ERROR` | CI/test infra issue |
| `DATA_ERROR` | Test data problem |
| `PERMISSION_ERROR` | Missing permissions |
| `MEMORY_ERROR` | Memory-related crash |
| `ANIMATION_ISSUE` | Animation timing issue |
| `UNKNOWN` | Unclassified failure |

## Output Examples

### Console Output

```
╭─────────────────────────────────────────────────────────────────╮
│                    Test Analysis Report                         │
╰─────────────────────────────────────────────────────────────────╯

Summary
┏━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric        ┃ Value ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━┩
│ Total Tests   │ 100   │
│ Passed        │ 85    │
│ Failed        │ 15    │
│ Pass Rate     │ 85.0% │
│ Flaky Tests   │ 3     │
└───────────────┴───────┘

Top Failure Categories
  • missing_element: 5 failures
  • timeout: 4 failures
  • assertion_failure: 3 failures
```

### Markdown Output

```markdown
# Test Analysis Report

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | 100 |
| Passed | 85 |
| Failed | 15 |
| Pass Rate | 85.0% |

## Failures

### 1. testLogin (AuthTests)

**Category:** TIMEOUT
**Severity:** MEDIUM
**Message:** Timed out waiting for login button

#### Suggestion: Increase Wait Timeout

The default timeout may be too short for this operation...
```

### JSON Output

```json
{
  "report": {
    "generated_at": "2024-01-15T10:30:00",
    "source": "tests.log"
  },
  "summary": {
    "total_tests": 100,
    "passed": 85,
    "failed": 15,
    "pass_rate": 85.0
  },
  "failures": [
    {
      "test_name": "testLogin",
      "test_class": "AuthTests",
      "category": "timeout",
      "severity": "medium",
      "message": "Timed out waiting for login button"
    }
  ]
}
```

## Debugging Suggestions

The tool provides context-aware debugging suggestions based on failure patterns:

```
┌─ Suggestion: Handle System Alerts ─────────────────────────────┐
│                                                                 │
│ System alerts can interrupt test execution. Add an interrupt   │
│ handler to automatically dismiss them.                         │
│                                                                 │
│ Action:                                                         │
│   Add interrupt handler in setUp():                            │
│                                                                 │
│   addUIInterruptionMonitor(withDescription: "Alert") { alert in│
│       alert.buttons["Allow"].tap()                             │
│       return true                                               │
│   }                                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=xcresult_ai_assistant --cov-report=html

# Run specific test file
pytest tests/test_analyzers.py -v
```

### Project Structure

```
xcresult-ai-assistant/
├── src/xcresult_ai_assistant/
│   ├── models/           # Pydantic data models
│   │   ├── test_result.py
│   │   ├── failure.py
│   │   ├── analysis.py
│   │   └── report.py
│   ├── parsers/          # Input format parsers
│   │   ├── log_parser.py
│   │   ├── junit_parser.py
│   │   ├── xcresult_parser.py
│   │   └── auto_parser.py
│   ├── analyzers/        # Failure analysis
│   │   ├── pattern_analyzer.py
│   │   ├── failure_analyzer.py
│   │   └── flaky_detector.py
│   ├── ai/               # Suggestion engine
│   │   └── suggestion_engine.py
│   ├── reports/          # Report generators
│   │   ├── console_reporter.py
│   │   ├── markdown_reporter.py
│   │   ├── json_reporter.py
│   │   └── report_factory.py
│   └── cli.py            # Typer CLI
├── tests/                # Pytest test suite
└── examples/             # Example input files
```

## Integration

### CI/CD Integration

Use JSON output for CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run tests
  run: xcodebuild test -scheme MyApp -resultBundlePath results.xcresult

- name: Analyze results
  run: |
    pip install xcresult-ai-assistant
    xcresult-ai analyze results.xcresult --format json --output analysis.json

- name: Upload analysis
  uses: actions/upload-artifact@v3
  with:
    name: test-analysis
    path: analysis.json
```

### Python API

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

# Generate report
report = ReportFactory.generate_report(analysis, ReportFormat.MARKDOWN)
print(report.content)
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting a pull request.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

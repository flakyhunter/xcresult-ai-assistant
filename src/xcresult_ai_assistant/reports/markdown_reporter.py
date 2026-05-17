"""Markdown report generator."""

from __future__ import annotations

from datetime import datetime

from xcresult_ai_assistant.models.analysis import AnalysisResult
from xcresult_ai_assistant.models.failure import FailureSeverity
from xcresult_ai_assistant.models.report import AnalysisReport, ReportConfig, ReportFormat


class MarkdownReporter:
    """Reporter that generates Markdown output."""

    def __init__(self, config: ReportConfig | None = None):
        """Initialize reporter."""
        self.config = config or ReportConfig(format=ReportFormat.MARKDOWN)

    def generate(self, analysis: AnalysisResult) -> AnalysisReport:
        """Generate markdown report."""
        sections: dict[str, str] = {}
        lines: list[str] = []

        # Header
        lines.append(f"# {self.config.title}")
        lines.append("")
        lines.append(f"*Generated: {analysis.timestamp.strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append(f"*Source: `{analysis.source_path}`*")
        lines.append("")

        # Summary section
        summary = self._generate_summary(analysis)
        sections["summary"] = summary
        lines.append(summary)

        # Quick stats
        stats = self._generate_stats(analysis)
        sections["stats"] = stats
        lines.append(stats)

        # Failures section
        if analysis.failures:
            failures = self._generate_failures(analysis)
            sections["failures"] = failures
            lines.append(failures)

            # Categories breakdown
            if self.config.group_by_category and analysis.category_summary:
                categories = self._generate_categories(analysis)
                sections["categories"] = categories
                lines.append(categories)

            # Suggestions section
            if self.config.include_suggestions and analysis.root_causes:
                suggestions = self._generate_suggestions(analysis)
                sections["suggestions"] = suggestions
                lines.append(suggestions)

        # Flaky analysis
        if analysis.flaky_count > 0:
            flaky = self._generate_flaky_section(analysis)
            sections["flaky"] = flaky
            lines.append(flaky)

        content = "\n".join(lines)

        return AnalysisReport(
            title=self.config.title,
            format=ReportFormat.MARKDOWN,
            analysis=analysis,
            config=self.config,
            content=content,
            sections=sections,
        )

    def _generate_summary(self, analysis: AnalysisResult) -> str:
        """Generate summary section."""
        lines = []

        # Overall status
        if analysis.failed_tests == 0:
            lines.append("## ✅ All Tests Passed")
        else:
            lines.append("## ❌ Test Failures Detected")

        lines.append("")
        return "\n".join(lines)

    def _generate_stats(self, analysis: AnalysisResult) -> str:
        """Generate statistics table."""
        lines = []
        lines.append("### Summary")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Total Tests | {analysis.total_tests} |")
        lines.append(f"| Passed | {analysis.passed_tests} |")
        lines.append(f"| Failed | {analysis.failed_tests} |")
        lines.append(f"| Skipped | {analysis.skipped_tests} |")

        if self.config.show_pass_rate:
            rate = analysis.pass_rate
            emoji = "🟢" if rate >= 90 else "🟡" if rate >= 70 else "🔴"
            lines.append(f"| Pass Rate | {emoji} {rate:.1f}% |")

        if analysis.flaky_count > 0:
            lines.append(f"| Likely Flaky | ⚠️ {analysis.flaky_count} |")

        if analysis.app_bugs_count > 0:
            lines.append(f"| Likely App Bugs | 🐛 {analysis.app_bugs_count} |")

        if analysis.infrastructure_count > 0:
            lines.append(f"| Infrastructure Issues | 🔧 {analysis.infrastructure_count} |")

        lines.append("")
        return "\n".join(lines)

    def _generate_failures(self, analysis: AnalysisResult) -> str:
        """Generate failures section."""
        lines = []
        lines.append("### Failures")
        lines.append("")

        failures = analysis.prioritized_failures
        if self.config.max_failures:
            failures = failures[: self.config.max_failures]

        for failure in failures:
            # Severity emoji
            severity_emoji = {
                FailureSeverity.CRITICAL: "🔴",
                FailureSeverity.HIGH: "🟠",
                FailureSeverity.MEDIUM: "🟡",
                FailureSeverity.LOW: "🔵",
                FailureSeverity.INFO: "⚪",
            }
            emoji = severity_emoji.get(failure.severity, "⚪")

            lines.append(f"#### {emoji} {failure.full_name}")
            lines.append("")
            lines.append(f"- **Category:** `{failure.category.value}`")
            lines.append(f"- **Severity:** {failure.severity.value}")

            if failure.message:
                msg = failure.message.replace("\n", " ")[:200]
                lines.append(f"- **Message:** {msg}")

            if failure.location != "unknown":
                lines.append(f"- **Location:** `{failure.location}`")

            # Indicators
            indicators = []
            if failure.is_flaky:
                indicators.append("⚠️ Flaky")
            if failure.is_app_issue:
                indicators.append("🐛 App Bug")
            if failure.is_infrastructure:
                indicators.append("🔧 Infrastructure")
            if failure.is_test_issue:
                indicators.append("🧪 Test Issue")

            if indicators:
                lines.append(f"- **Indicators:** {', '.join(indicators)}")

            # Stack trace
            if self.config.include_stack_traces and failure.stack_trace:
                lines.append("")
                lines.append("<details>")
                lines.append("<summary>Stack Trace</summary>")
                lines.append("")
                lines.append("```")
                lines.append(failure.stack_trace[:1000])
                if len(failure.stack_trace) > 1000:
                    lines.append("... (truncated)")
                lines.append("```")
                lines.append("")
                lines.append("</details>")

            lines.append("")

        if len(analysis.failures) > self.config.max_failures:
            remaining = len(analysis.failures) - self.config.max_failures
            lines.append(f"*... and {remaining} more failures*")
            lines.append("")

        return "\n".join(lines)

    def _generate_categories(self, analysis: AnalysisResult) -> str:
        """Generate categories breakdown."""
        lines = []
        lines.append("### Failures by Category")
        lines.append("")
        lines.append("| Category | Count | % |")
        lines.append("|----------|-------|---|")

        total = sum(analysis.category_summary.values())
        for category, count in analysis.top_categories:
            pct = (count / total * 100) if total > 0 else 0
            lines.append(f"| {category} | {count} | {pct:.1f}% |")

        lines.append("")
        return "\n".join(lines)

    def _generate_suggestions(self, analysis: AnalysisResult) -> str:
        """Generate suggestions section."""
        lines = []
        lines.append("### 💡 Debugging Suggestions")
        lines.append("")

        for rca in analysis.root_causes[:5]:
            lines.append(f"#### {rca.summary}")
            lines.append("")

            if rca.detailed_explanation:
                lines.append(f"> {rca.detailed_explanation}")
                lines.append("")

            if rca.suggestions:
                lines.append("**Recommended Actions:**")
                lines.append("")
                for suggestion in rca.suggestions[:3]:
                    lines.append(f"1. **{suggestion.title}**")
                    lines.append(f"   - {suggestion.description}")
                    if suggestion.action:
                        lines.append(f"   - Action: {suggestion.action}")
                    if suggestion.code_example:
                        lines.append("   ```swift")
                        lines.append(f"   {suggestion.code_example}")
                        lines.append("   ```")
                lines.append("")

            if rca.evidence:
                lines.append("<details>")
                lines.append("<summary>Evidence</summary>")
                lines.append("")
                for e in rca.evidence:
                    lines.append(f"- {e}")
                lines.append("")
                lines.append("</details>")
                lines.append("")

        return "\n".join(lines)

    def _generate_flaky_section(self, analysis: AnalysisResult) -> str:
        """Generate flaky tests section."""
        lines = []
        lines.append("### ⚠️ Potentially Flaky Tests")
        lines.append("")
        lines.append(
            f"Found {analysis.flaky_count} tests that exhibit flaky behavior patterns."
        )
        lines.append("")

        flaky_failures = [f for f in analysis.failures if f.is_flaky]
        for failure in flaky_failures[:10]:
            lines.append(f"- `{failure.full_name}` ({failure.category.value})")

        lines.append("")
        lines.append("**Common remediation:**")
        lines.append("- Add explicit waits for async operations")
        lines.append("- Mock network responses")
        lines.append("- Handle system interruptions")
        lines.append("- Improve test isolation")
        lines.append("")

        return "\n".join(lines)

"""HTML report generator with styled, interactive output."""

from __future__ import annotations

import html
from datetime import datetime

from xcresult_ai_assistant.models.analysis import AnalysisResult
from xcresult_ai_assistant.models.failure import FailureSeverity
from xcresult_ai_assistant.models.report import AnalysisReport, ReportConfig, ReportFormat


class HtmlReporter:
    """Reporter that generates styled HTML output."""

    def __init__(self, config: ReportConfig | None = None):
        """Initialize reporter."""
        self.config = config or ReportConfig(format=ReportFormat.HTML)

    def generate(self, analysis: AnalysisResult) -> AnalysisReport:
        """Generate HTML report."""
        sections: dict[str, str] = {}

        # Build HTML document
        html_parts = [
            self._generate_head(analysis),
            '<body>',
            '<div class="container">',
            self._generate_header(analysis),
        ]

        # Summary section
        summary = self._generate_summary(analysis)
        sections["summary"] = summary
        html_parts.append(summary)

        # Stats cards
        stats = self._generate_stats_cards(analysis)
        sections["stats"] = stats
        html_parts.append(stats)

        # Top findings
        if analysis.failures:
            top_findings = self._generate_top_findings(analysis)
            sections["top_findings"] = top_findings
            html_parts.append(top_findings)

            # Categories breakdown
            if self.config.group_by_category and analysis.category_summary:
                categories = self._generate_categories(analysis)
                sections["categories"] = categories
                html_parts.append(categories)

            # Failures table
            failures = self._generate_failures_table(analysis)
            sections["failures"] = failures
            html_parts.append(failures)

            # Suggestions section
            if self.config.include_suggestions and analysis.root_causes:
                suggestions = self._generate_suggestions(analysis)
                sections["suggestions"] = suggestions
                html_parts.append(suggestions)

        # Flaky analysis
        if analysis.flaky_count > 0:
            flaky = self._generate_flaky_section(analysis)
            sections["flaky"] = flaky
            html_parts.append(flaky)

        html_parts.extend([
            '</div>',
            self._generate_footer(),
            '</body>',
            '</html>',
        ])

        content = '\n'.join(html_parts)

        return AnalysisReport(
            title=self.config.title,
            format=ReportFormat.HTML,
            analysis=analysis,
            config=self.config,
            content=content,
            sections=sections,
        )

    def _generate_head(self, analysis: AnalysisResult) -> str:
        """Generate HTML head with embedded styles."""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(self.config.title)}</title>
    <style>
        :root {{
            --color-success: #22c55e;
            --color-warning: #f59e0b;
            --color-error: #ef4444;
            --color-info: #3b82f6;
            --color-muted: #6b7280;
            --color-bg: #f9fafb;
            --color-card: #ffffff;
            --color-border: #e5e7eb;
            --color-text: #111827;
            --color-text-muted: #6b7280;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--color-bg);
            color: var(--color-text);
            line-height: 1.6;
            padding: 2rem;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
        h2 {{ font-size: 1.5rem; margin: 2rem 0 1rem; color: var(--color-text); }}
        h3 {{ font-size: 1.25rem; margin: 1.5rem 0 0.75rem; }}
        .subtitle {{ color: var(--color-text-muted); margin-bottom: 2rem; }}

        /* Status Badge */
        .status-badge {{
            display: inline-block;
            padding: 0.5rem 1rem;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 1rem;
            margin-bottom: 1.5rem;
        }}
        .status-success {{ background: #dcfce7; color: #166534; }}
        .status-failure {{ background: #fee2e2; color: #991b1b; }}

        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin: 1.5rem 0;
        }}
        .stat-card {{
            background: var(--color-card);
            border: 1px solid var(--color-border);
            border-radius: 0.75rem;
            padding: 1.25rem;
            text-align: center;
        }}
        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.2;
        }}
        .stat-label {{ color: var(--color-text-muted); font-size: 0.875rem; }}
        .stat-success .stat-value {{ color: var(--color-success); }}
        .stat-error .stat-value {{ color: var(--color-error); }}
        .stat-warning .stat-value {{ color: var(--color-warning); }}
        .stat-info .stat-value {{ color: var(--color-info); }}

        /* Progress Bar */
        .progress-bar {{
            height: 8px;
            background: var(--color-border);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 0.5rem;
        }}
        .progress-fill {{
            height: 100%;
            transition: width 0.3s;
        }}
        .progress-success {{ background: var(--color-success); }}
        .progress-warning {{ background: var(--color-warning); }}
        .progress-error {{ background: var(--color-error); }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--color-card);
            border-radius: 0.75rem;
            overflow: hidden;
            margin: 1rem 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 0.75rem 1rem;
            text-align: left;
            border-bottom: 1px solid var(--color-border);
        }}
        th {{ background: var(--color-bg); font-weight: 600; }}
        tr:hover {{ background: #f3f4f6; }}
        tr:last-child td {{ border-bottom: none; }}

        /* Severity Badges */
        .severity {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .severity-critical {{ background: #fee2e2; color: #991b1b; }}
        .severity-high {{ background: #ffedd5; color: #9a3412; }}
        .severity-medium {{ background: #fef3c7; color: #92400e; }}
        .severity-low {{ background: #dbeafe; color: #1e40af; }}
        .severity-info {{ background: #f3f4f6; color: #374151; }}

        /* Category Tag */
        .category-tag {{
            display: inline-block;
            padding: 0.25rem 0.5rem;
            background: #e0e7ff;
            color: #3730a3;
            border-radius: 0.375rem;
            font-size: 0.75rem;
            font-family: monospace;
        }}

        /* Indicator Pills */
        .indicators {{ display: flex; gap: 0.5rem; flex-wrap: wrap; }}
        .indicator {{
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
            padding: 0.25rem 0.5rem;
            border-radius: 9999px;
            font-size: 0.75rem;
        }}
        .indicator-flaky {{ background: #fef3c7; color: #92400e; }}
        .indicator-bug {{ background: #fee2e2; color: #991b1b; }}
        .indicator-infra {{ background: #dbeafe; color: #1e40af; }}
        .indicator-test {{ background: #d1fae5; color: #065f46; }}

        /* Cards */
        .card {{
            background: var(--color-card);
            border: 1px solid var(--color-border);
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin: 1rem 0;
        }}
        .card-title {{ font-weight: 600; margin-bottom: 0.75rem; }}

        /* Collapsible */
        details {{
            background: var(--color-card);
            border: 1px solid var(--color-border);
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }}
        summary {{
            padding: 0.75rem 1rem;
            cursor: pointer;
            font-weight: 500;
        }}
        summary:hover {{ background: var(--color-bg); }}
        details[open] summary {{ border-bottom: 1px solid var(--color-border); }}
        .details-content {{ padding: 1rem; }}

        /* Code Block */
        pre {{
            background: #1f2937;
            color: #f9fafb;
            padding: 1rem;
            border-radius: 0.5rem;
            overflow-x: auto;
            font-size: 0.875rem;
            margin: 0.5rem 0;
        }}
        code {{
            font-family: 'SF Mono', Monaco, Consolas, monospace;
        }}

        /* Top Findings */
        .finding-card {{
            background: var(--color-card);
            border: 1px solid var(--color-border);
            border-left: 4px solid;
            border-radius: 0.5rem;
            padding: 1rem 1.25rem;
            margin: 0.75rem 0;
        }}
        .finding-critical {{ border-left-color: var(--color-error); }}
        .finding-high {{ border-left-color: #f97316; }}
        .finding-medium {{ border-left-color: var(--color-warning); }}
        .finding-title {{ font-weight: 600; margin-bottom: 0.5rem; }}
        .finding-meta {{ color: var(--color-text-muted); font-size: 0.875rem; }}

        /* Suggestion Card */
        .suggestion {{
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 0.75rem;
            padding: 1.25rem;
            margin: 1rem 0;
        }}
        .suggestion-title {{
            font-weight: 600;
            color: #1e40af;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .suggestion-action {{
            margin-top: 0.75rem;
            padding: 0.75rem;
            background: #dbeafe;
            border-radius: 0.5rem;
        }}

        /* Footer */
        .footer {{
            margin-top: 3rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--color-border);
            color: var(--color-text-muted);
            font-size: 0.875rem;
            text-align: center;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            body {{ padding: 1rem; }}
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
            table {{ font-size: 0.875rem; }}
            th, td {{ padding: 0.5rem; }}
        }}
    </style>
</head>'''

    def _generate_header(self, analysis: AnalysisResult) -> str:
        """Generate page header."""
        timestamp = analysis.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        return f'''
<header>
    <h1>{html.escape(self.config.title)}</h1>
    <p class="subtitle">
        Generated: {timestamp} &bull;
        Source: <code>{html.escape(str(analysis.source_path))}</code>
    </p>
</header>'''

    def _generate_summary(self, analysis: AnalysisResult) -> str:
        """Generate summary section."""
        if analysis.failed_tests == 0:
            return '''
<div class="status-badge status-success">
    ✅ All Tests Passed
</div>'''
        else:
            return f'''
<div class="status-badge status-failure">
    ❌ {analysis.failed_tests} Test Failure{"s" if analysis.failed_tests != 1 else ""} Detected
</div>'''

    def _generate_stats_cards(self, analysis: AnalysisResult) -> str:
        """Generate statistics cards."""
        rate = analysis.pass_rate
        rate_class = "success" if rate >= 90 else "warning" if rate >= 70 else "error"
        progress_class = f"progress-{rate_class}"

        cards = [
            f'''<div class="stat-card">
                <div class="stat-value">{analysis.total_tests}</div>
                <div class="stat-label">Total Tests</div>
            </div>''',
            f'''<div class="stat-card stat-success">
                <div class="stat-value">{analysis.passed_tests}</div>
                <div class="stat-label">Passed</div>
            </div>''',
            f'''<div class="stat-card stat-error">
                <div class="stat-value">{analysis.failed_tests}</div>
                <div class="stat-label">Failed</div>
            </div>''',
            f'''<div class="stat-card stat-{rate_class}">
                <div class="stat-value">{rate:.1f}%</div>
                <div class="stat-label">Pass Rate</div>
                <div class="progress-bar">
                    <div class="progress-fill {progress_class}" style="width: {rate}%"></div>
                </div>
            </div>''',
        ]

        if analysis.flaky_count > 0:
            cards.append(f'''<div class="stat-card stat-warning">
                <div class="stat-value">{analysis.flaky_count}</div>
                <div class="stat-label">Likely Flaky</div>
            </div>''')

        if analysis.app_bugs_count > 0:
            cards.append(f'''<div class="stat-card stat-error">
                <div class="stat-value">{analysis.app_bugs_count}</div>
                <div class="stat-label">App Bugs</div>
            </div>''')

        return f'''
<div class="stats-grid">
    {''.join(cards)}
</div>'''

    def _generate_top_findings(self, analysis: AnalysisResult) -> str:
        """Generate top findings section."""
        critical = analysis.critical_failures[:3]
        if not critical:
            return ""

        findings = []
        for f in critical:
            sev = f.severity.value.lower()
            findings.append(f'''
<div class="finding-card finding-{sev}">
    <div class="finding-title">{html.escape(f.full_name)}</div>
    <div class="finding-meta">
        <span class="category-tag">{f.category.value}</span>
        <span class="severity severity-{sev}">{f.severity.value}</span>
    </div>
    <p style="margin-top: 0.5rem; color: var(--color-text-muted);">
        {html.escape(f.message[:150] + '...' if len(f.message) > 150 else f.message)}
    </p>
</div>''')

        return f'''
<h2>🔥 Top Findings</h2>
<p style="color: var(--color-text-muted);">Most critical issues requiring immediate attention</p>
{''.join(findings)}'''

    def _generate_categories(self, analysis: AnalysisResult) -> str:
        """Generate category breakdown table."""
        total = sum(analysis.category_summary.values())
        rows = []

        for category, count in analysis.top_categories[:10]:
            pct = (count / total * 100) if total > 0 else 0
            rows.append(f'''
<tr>
    <td><span class="category-tag">{category}</span></td>
    <td>{count}</td>
    <td>
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <div class="progress-bar" style="width: 100px; height: 6px;">
                <div class="progress-fill progress-info" style="width: {pct}%"></div>
            </div>
            <span>{pct:.1f}%</span>
        </div>
    </td>
</tr>''')

        return f'''
<h2>📊 Failures by Category</h2>
<table>
    <thead>
        <tr>
            <th>Category</th>
            <th>Count</th>
            <th>Distribution</th>
        </tr>
    </thead>
    <tbody>
        {''.join(rows)}
    </tbody>
</table>'''

    def _generate_failures_table(self, analysis: AnalysisResult) -> str:
        """Generate failures table."""
        failures = analysis.prioritized_failures
        if self.config.max_failures:
            failures = failures[:self.config.max_failures]

        rows = []
        for f in failures:
            sev = f.severity.value.lower()

            indicators = []
            if f.is_flaky:
                indicators.append('<span class="indicator indicator-flaky">⚠️ Flaky</span>')
            if f.is_app_issue:
                indicators.append('<span class="indicator indicator-bug">🐛 Bug</span>')
            if f.is_infrastructure:
                indicators.append('<span class="indicator indicator-infra">🔧 Infra</span>')

            indicators_html = f'<div class="indicators">{"".join(indicators)}</div>' if indicators else ''

            stack_trace = ""
            if self.config.include_stack_traces and f.stack_trace:
                trace = html.escape(f.stack_trace[:500])
                stack_trace = f'''
<details style="margin-top: 0.5rem;">
    <summary>Stack Trace</summary>
    <div class="details-content">
        <pre><code>{trace}{"..." if len(f.stack_trace) > 500 else ""}</code></pre>
    </div>
</details>'''

            rows.append(f'''
<tr>
    <td>
        <strong>{html.escape(f.full_name)}</strong>
        {indicators_html}
        {stack_trace}
    </td>
    <td><span class="category-tag">{f.category.value}</span></td>
    <td><span class="severity severity-{sev}">{f.severity.value}</span></td>
    <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis;">
        {html.escape(f.message[:100])}{"..." if len(f.message) > 100 else ""}
    </td>
    <td><code>{html.escape(f.location)}</code></td>
</tr>''')

        remaining = ""
        if len(analysis.failures) > self.config.max_failures:
            remaining = f'<p style="color: var(--color-text-muted); margin-top: 1rem;">...and {len(analysis.failures) - self.config.max_failures} more failures</p>'

        return f'''
<h2>📋 All Failures</h2>
<table>
    <thead>
        <tr>
            <th>Test</th>
            <th>Category</th>
            <th>Severity</th>
            <th>Message</th>
            <th>Location</th>
        </tr>
    </thead>
    <tbody>
        {''.join(rows)}
    </tbody>
</table>
{remaining}'''

    def _generate_suggestions(self, analysis: AnalysisResult) -> str:
        """Generate suggestions section."""
        suggestions = []

        for rca in analysis.root_causes[:5]:
            suggestion_items = []
            for s in rca.suggestions[:3]:
                code_block = ""
                if s.code_example:
                    code_block = f'<pre><code>{html.escape(s.code_example)}</code></pre>'

                suggestion_items.append(f'''
<div class="suggestion">
    <div class="suggestion-title">
        💡 {html.escape(s.title)}
    </div>
    <p>{html.escape(s.description)}</p>
    {f'<div class="suggestion-action"><strong>Action:</strong> {html.escape(s.action)}</div>' if s.action else ''}
    {code_block}
</div>''')

            if suggestion_items:
                suggestions.append(f'''
<div class="card">
    <div class="card-title">{html.escape(rca.summary)}</div>
    <p style="color: var(--color-text-muted);">{html.escape(rca.detailed_explanation or '')}</p>
    {''.join(suggestion_items)}
</div>''')

        return f'''
<h2>💡 Debugging Suggestions</h2>
<p style="color: var(--color-text-muted);">AI-powered recommendations based on failure patterns</p>
{''.join(suggestions)}'''

    def _generate_flaky_section(self, analysis: AnalysisResult) -> str:
        """Generate flaky tests section."""
        flaky_tests = [f for f in analysis.failures if f.is_flaky][:10]

        items = []
        for f in flaky_tests:
            items.append(f'''
<tr>
    <td><code>{html.escape(f.full_name)}</code></td>
    <td><span class="category-tag">{f.category.value}</span></td>
    <td>{f.confidence:.0%}</td>
</tr>''')

        return f'''
<h2>⚠️ Potentially Flaky Tests</h2>
<p style="color: var(--color-text-muted);">
    Found {analysis.flaky_count} tests exhibiting flaky behavior patterns.
    These tests may pass/fail inconsistently.
</p>
<table>
    <thead>
        <tr>
            <th>Test</th>
            <th>Category</th>
            <th>Confidence</th>
        </tr>
    </thead>
    <tbody>
        {''.join(items)}
    </tbody>
</table>
<div class="card" style="margin-top: 1rem;">
    <div class="card-title">Common Remediation Steps</div>
    <ul style="margin: 0.5rem 0 0 1.5rem;">
        <li>Add explicit waits for async operations</li>
        <li>Mock network responses for deterministic testing</li>
        <li>Handle system interruptions (alerts, notifications)</li>
        <li>Improve test isolation and cleanup</li>
    </ul>
</div>'''

    def _generate_footer(self) -> str:
        """Generate page footer."""
        return '''
<footer class="footer">
    <p>Generated by <strong>XCResult AI Assistant</strong></p>
    <p>
        <a href="https://github.com/flakyhunter/xcresult-ai-assistant" target="_blank">
            GitHub
        </a>
    </p>
</footer>'''

"""JSON report generator."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from xcresult_ai_assistant.models.analysis import AnalysisResult
from xcresult_ai_assistant.models.report import AnalysisReport, ReportConfig, ReportFormat


class JsonReporter:
    """Reporter that generates JSON output."""

    def __init__(self, config: ReportConfig | None = None):
        """Initialize reporter."""
        self.config = config or ReportConfig(format=ReportFormat.JSON)

    def generate(self, analysis: AnalysisResult) -> AnalysisReport:
        """Generate JSON report."""
        data = self._build_json_structure(analysis)
        content = json.dumps(data, indent=2, default=self._json_serializer)

        return AnalysisReport(
            title=self.config.title,
            format=ReportFormat.JSON,
            analysis=analysis,
            config=self.config,
            content=content,
            sections={"json": content},
        )

    def _build_json_structure(self, analysis: AnalysisResult) -> dict[str, Any]:
        """Build the JSON data structure."""
        data: dict[str, Any] = {
            "report": {
                "title": self.config.title,
                "generated_at": analysis.timestamp.isoformat(),
                "source": analysis.source_path,
                "version": "1.0",
            },
            "summary": {
                "total_tests": analysis.total_tests,
                "passed": analysis.passed_tests,
                "failed": analysis.failed_tests,
                "skipped": analysis.skipped_tests,
                "pass_rate": round(analysis.pass_rate, 2),
                "failure_rate": round(analysis.failure_rate, 2),
                "analysis_duration_seconds": round(analysis.analysis_duration, 3),
            },
            "breakdown": {
                "flaky_count": analysis.flaky_count,
                "infrastructure_issues": analysis.infrastructure_count,
                "app_bugs": analysis.app_bugs_count,
                "categories": analysis.category_summary,
                "severities": analysis.severity_summary,
            },
        }

        # Add failures
        failures_data = []
        for failure in analysis.failures[: self.config.max_failures]:
            failure_dict: dict[str, Any] = {
                "test_name": failure.test_name,
                "test_class": failure.test_class,
                "full_name": failure.full_name,
                "category": failure.category.value,
                "severity": failure.severity.value,
                "confidence": round(failure.confidence, 2),
                "priority_score": failure.priority_score,
                "indicators": {
                    "is_flaky": failure.is_flaky,
                    "is_infrastructure": failure.is_infrastructure,
                    "is_test_issue": failure.is_test_issue,
                    "is_app_issue": failure.is_app_issue,
                },
            }

            if failure.message:
                failure_dict["message"] = failure.message

            if failure.location != "unknown":
                failure_dict["location"] = {
                    "file": failure.file_path,
                    "line": failure.line_number,
                }

            if self.config.include_stack_traces and failure.stack_trace:
                failure_dict["stack_trace"] = failure.stack_trace

            if failure.matched_patterns:
                failure_dict["matched_patterns"] = failure.matched_patterns

            if failure.related_elements:
                failure_dict["related_elements"] = failure.related_elements

            if failure.duration > 0:
                failure_dict["duration_seconds"] = round(failure.duration, 3)

            failures_data.append(failure_dict)

        data["failures"] = failures_data

        # Add suggestions
        if self.config.include_suggestions and analysis.root_causes:
            suggestions_data = []
            for rca in analysis.root_causes:
                rca_dict: dict[str, Any] = {
                    "category": rca.category.value,
                    "summary": rca.summary,
                    "confidence": rca.confidence.value,
                    "is_flaky_indicator": rca.is_flaky_indicator,
                    "requires_investigation": rca.requires_investigation,
                    "affected_tests": rca.affected_components,
                }

                if rca.detailed_explanation:
                    rca_dict["explanation"] = rca.detailed_explanation

                if rca.evidence:
                    rca_dict["evidence"] = rca.evidence

                if rca.suggestions:
                    rca_dict["suggestions"] = [
                        {
                            "title": s.title,
                            "description": s.description,
                            "action": s.action,
                            "priority": s.priority,
                            "confidence": s.confidence.value,
                            "tags": s.tags,
                        }
                        for s in rca.suggestions
                    ]

                suggestions_data.append(rca_dict)

            data["root_cause_analysis"] = suggestions_data

        # Add metadata
        if analysis.metadata:
            data["metadata"] = analysis.metadata

        return data

    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for non-standard types."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "value"):  # Enum
            return obj.value
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def generate_minimal(self, analysis: AnalysisResult) -> str:
        """Generate minimal JSON output (just summary)."""
        data = {
            "status": "passed" if analysis.failed_tests == 0 else "failed",
            "total": analysis.total_tests,
            "passed": analysis.passed_tests,
            "failed": analysis.failed_tests,
            "pass_rate": round(analysis.pass_rate, 2),
        }
        return json.dumps(data)

    def generate_failures_only(self, analysis: AnalysisResult) -> str:
        """Generate JSON with only failure details."""
        failures = [
            {
                "name": f.full_name,
                "category": f.category.value,
                "severity": f.severity.value,
                "message": f.message,
            }
            for f in analysis.failures
        ]
        return json.dumps({"failures": failures}, indent=2)

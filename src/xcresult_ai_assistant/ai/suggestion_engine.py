"""AI-style suggestion engine for debugging recommendations."""

from __future__ import annotations

from xcresult_ai_assistant.models.analysis import ConfidenceLevel, DebugSuggestion
from xcresult_ai_assistant.models.failure import FailureCategory


class SuggestionEngine:
    """Engine for generating debugging suggestions based on failure patterns."""

    def __init__(self) -> None:
        """Initialize suggestion engine with knowledge base."""
        self.knowledge_base = self._build_knowledge_base()

    def _build_knowledge_base(self) -> dict[FailureCategory, list[DebugSuggestion]]:
        """Build comprehensive suggestion knowledge base."""
        return {
            FailureCategory.MISSING_ELEMENT: [
                DebugSuggestion(
                    title="Verify accessibility identifier",
                    description=(
                        "The element may not have the expected accessibility identifier. "
                        "Check that the identifier is set correctly in the view code."
                    ),
                    action="Search for the identifier in your SwiftUI/UIKit code and verify it matches",
                    code_example='.accessibilityIdentifier("myButtonId")',
                    priority=1,
                    category="accessibility",
                    confidence=ConfidenceLevel.HIGH,
                    tags=["accessibility", "identifier", "swiftui"],
                ),
                DebugSuggestion(
                    title="Add wait for element existence",
                    description=(
                        "The element might not be rendered yet when the test tries to find it. "
                        "Add an explicit wait for the element to appear."
                    ),
                    action="Use waitForExistence(timeout:) before interacting with the element",
                    code_example="XCTAssertTrue(element.waitForExistence(timeout: 5))",
                    priority=2,
                    category="timing",
                    confidence=ConfidenceLevel.HIGH,
                    tags=["wait", "timing", "existence"],
                ),
                DebugSuggestion(
                    title="Check navigation state",
                    description=(
                        "The test might be looking for an element on a screen that hasn't "
                        "been navigated to yet, or the navigation may have failed."
                    ),
                    action="Verify the app is on the correct screen before querying elements",
                    priority=3,
                    category="navigation",
                    confidence=ConfidenceLevel.MEDIUM,
                    tags=["navigation", "screen", "state"],
                ),
                DebugSuggestion(
                    title="Check conditional UI",
                    description=(
                        "The element might only appear under certain conditions (e.g., "
                        "feature flags, user permissions, or data state)."
                    ),
                    action="Verify preconditions for the element to be displayed",
                    priority=4,
                    category="data",
                    confidence=ConfidenceLevel.MEDIUM,
                    tags=["conditional", "feature-flag", "permissions"],
                ),
            ],

            FailureCategory.ELEMENT_NOT_HITTABLE: [
                DebugSuggestion(
                    title="Wait for element to become hittable",
                    description=(
                        "The element exists but isn't ready for interaction. "
                        "This often happens during animations or loading states."
                    ),
                    action="Add a wait or check isHittable before tapping",
                    code_example=(
                        "let element = app.buttons[\"submit\"]\n"
                        "_ = element.waitForExistence(timeout: 5)\n"
                        "XCTAssertTrue(element.isHittable)"
                    ),
                    priority=1,
                    category="timing",
                    confidence=ConfidenceLevel.HIGH,
                    tags=["hittable", "animation", "wait"],
                ),
                DebugSuggestion(
                    title="Check for overlapping elements",
                    description=(
                        "Another element (like a loading overlay, keyboard, or popup) "
                        "might be covering the target element."
                    ),
                    action="Dismiss any overlays or check z-order of elements",
                    priority=2,
                    category="layout",
                    confidence=ConfidenceLevel.MEDIUM,
                    tags=["overlay", "keyboard", "popup"],
                ),
                DebugSuggestion(
                    title="Scroll element into view",
                    description=(
                        "The element might be outside the visible scroll area. "
                        "Try scrolling to bring it into view."
                    ),
                    action="Use swipeUp/swipeDown or scroll to element before tapping",
                    code_example=(
                        "while !element.isHittable {\n"
                        "    app.swipeUp()\n"
                        "}"
                    ),
                    priority=3,
                    category="layout",
                    confidence=ConfidenceLevel.MEDIUM,
                    tags=["scroll", "visible", "viewport"],
                ),
            ],

            FailureCategory.TIMEOUT: [
                DebugSuggestion(
                    title="Increase timeout duration",
                    description=(
                        "The default timeout may be too short for slow operations. "
                        "Consider increasing it for network-dependent operations."
                    ),
                    action="Increase the timeout value for waitForExistence or expectations",
                    code_example="element.waitForExistence(timeout: 10)",
                    priority=1,
                    category="timing",
                    confidence=ConfidenceLevel.MEDIUM,
                    tags=["timeout", "wait", "duration"],
                ),
                DebugSuggestion(
                    title="Check for loading states",
                    description=(
                        "The app might be stuck in a loading state. "
                        "Verify that loading completes before proceeding."
                    ),
                    action="Wait for loading indicators to disappear",
                    code_example=(
                        "let spinner = app.activityIndicators.firstMatch\n"
                        "expectation(for: NSPredicate(format: \"exists == false\"), "
                        "evaluatedWith: spinner)"
                    ),
                    priority=2,
                    category="loading",
                    confidence=ConfidenceLevel.HIGH,
                    tags=["loading", "spinner", "network"],
                ),
                DebugSuggestion(
                    title="Mock network responses",
                    description=(
                        "Timeouts often occur due to slow or unreliable network. "
                        "Consider mocking API responses for more reliable tests."
                    ),
                    action="Implement network mocking for deterministic test behavior",
                    priority=3,
                    category="network",
                    confidence=ConfidenceLevel.HIGH,
                    tags=["mock", "network", "api"],
                ),
            ],

            FailureCategory.WAIT_TIMEOUT: [
                DebugSuggestion(
                    title="Verify wait condition",
                    description=(
                        "The condition being waited for may never become true. "
                        "Check that the expected state is actually achievable."
                    ),
                    action="Debug the app state at the point of timeout",
                    priority=1,
                    category="debugging",
                    confidence=ConfidenceLevel.MEDIUM,
                    tags=["condition", "state", "debug"],
                ),
                DebugSuggestion(
                    title="Use more specific wait conditions",
                    description=(
                        "Generic waits may not capture the exact condition needed. "
                        "Use predicates for more precise waiting."
                    ),
                    action="Create a specific predicate for the condition",
                    code_example=(
                        "let predicate = NSPredicate(format: \"label == 'Success'\")\n"
                        "expectation(for: predicate, evaluatedWith: element)"
                    ),
                    priority=2,
                    category="timing",
                    confidence=ConfidenceLevel.HIGH,
                    tags=["predicate", "specific", "wait"],
                ),
            ],

            FailureCategory.ASSERTION_FAILURE: [
                DebugSuggestion(
                    title="Review expected vs actual values",
                    description=(
                        "The assertion failed because the actual value differs from expected. "
                        "This may indicate a bug or incorrect test expectation."
                    ),
                    action="Compare expected and actual values, check if expectation is correct",
                    priority=1,
                    category="verification",
                    confidence=ConfidenceLevel.HIGH,
                    tags=["assertion", "expected", "actual"],
                ),
                DebugSuggestion(
                    title="Check data state",
                    description=(
                        "The failure might be due to unexpected data state. "
                        "Verify that test fixtures and preconditions are correct."
                    ),
                    action="Review test setup and data fixtures",
                    priority=2,
                    category="data",
                    confidence=ConfidenceLevel.MEDIUM,
                    tags=["data", "fixture", "setup"],
                ),
                DebugSuggestion(
                    title="This may be an app bug",
                    description=(
                        "If the test expectation is correct, this assertion failure "
                        "indicates a bug in the application code."
                    ),
                    action="File a bug report with reproduction steps",
                    priority=3,
                    category="bug",
                    confidence=ConfidenceLevel.MEDIUM,
                    tags=["bug", "regression", "app"],
                ),
            ],

            FailureCategory.APP_CRASH: [
                DebugSuggestion(
                    title="Check crash logs",
                    description=(
                        "A crash occurred during test execution. "
                        "Examine the crash log for the root cause."
                    ),
                    action="Review crash log, symbolicate if needed, identify the crash point",
                    priority=1,
                    category="crash",
                    confidence=ConfidenceLevel.HIGH,
                    tags=["crash", "log", "symbolicate"],
                ),
                DebugSuggestion(
                    title="Check for force unwrapping",
                    description=(
                        "Crashes often result from force unwrapping nil optionals. "
                        "Search for '!' operators in the crash location."
                    ),
                    action="Replace force unwraps with safe unwrapping or guards",
                    code_example="guard let value = optional else { return }",
                    priority=2,
                    category="code",
                    confidence=ConfidenceLevel.HIGH,
                    tags=["optional", "unwrap", "nil"],
                ),
                DebugSuggestion(
                    title="Check thread safety",
                    description=(
                        "Crashes can occur from thread safety violations, "
                        "especially when updating UI from background threads."
                    ),
                    action="Ensure UI updates happen on main thread",
                    code_example="DispatchQueue.main.async { self.updateUI() }",
                    priority=3,
                    category="threading",
                    confidence=ConfidenceLevel.MEDIUM,
                    tags=["thread", "main", "async"],
                ),
            ],

            FailureCategory.NETWORK_ERROR: [
                DebugSuggestion(
                    title="Mock network for tests",
                    description=(
                        "Network tests are inherently flaky due to external dependencies. "
                        "Use mocked responses for reliable testing."
                    ),
                    action="Implement URLProtocol mock or use a mocking framework",
                    priority=1,
                    category="network",
                    confidence=ConfidenceLevel.HIGH,
                    tags=["mock", "urlprotocol", "network"],
                ),
                DebugSuggestion(
                    title="Add retry logic",
                    description=(
                        "For integration tests that need real network, "
                        "add retry logic to handle transient failures."
                    ),
                    action="Implement retry mechanism with exponential backoff",
                    priority=2,
                    category="resilience",
                    confidence=ConfidenceLevel.MEDIUM,
                    tags=["retry", "resilience", "transient"],
                ),
            ],

            FailureCategory.SYSTEM_ALERT: [
                DebugSuggestion(
                    title="Add UI interruption monitor",
                    description=(
                        "System alerts (permissions, notifications) can block test execution. "
                        "Handle them with an interruption monitor."
                    ),
                    action="Add addUIInterruptionMonitor in test setup",
                    code_example=(
                        "addUIInterruptionMonitor(withDescription: \"Alert\") { alert in\n"
                        "    alert.buttons[\"Allow\"].tap()\n"
                        "    return true\n"
                        "}"
                    ),
                    priority=1,
                    category="system",
                    confidence=ConfidenceLevel.HIGH,
                    tags=["alert", "permission", "interruption"],
                ),
                DebugSuggestion(
                    title="Disable notifications in simulator",
                    description=(
                        "Notifications can interfere with UI tests. "
                        "Configure simulator to suppress notifications."
                    ),
                    action="Reset simulator or disable notification permissions",
                    priority=2,
                    category="environment",
                    confidence=ConfidenceLevel.MEDIUM,
                    tags=["notification", "simulator", "config"],
                ),
            ],

            FailureCategory.SNAPSHOT_MISMATCH: [
                DebugSuggestion(
                    title="Review visual diff",
                    description=(
                        "A snapshot comparison failed. "
                        "Check the diff image to determine if this is a real change."
                    ),
                    action="Compare reference, actual, and diff images",
                    priority=1,
                    category="visual",
                    confidence=ConfidenceLevel.HIGH,
                    tags=["snapshot", "diff", "visual"],
                ),
                DebugSuggestion(
                    title="Update reference if intentional",
                    description=(
                        "If the visual change is intentional, "
                        "update the reference snapshot."
                    ),
                    action="Run tests with recording mode enabled",
                    code_example="isRecording = true  // in test setup",
                    priority=2,
                    category="snapshot",
                    confidence=ConfidenceLevel.MEDIUM,
                    tags=["record", "reference", "update"],
                ),
                DebugSuggestion(
                    title="Check for platform-specific rendering",
                    description=(
                        "Snapshot tests can fail due to differences in "
                        "iOS versions, device types, or font rendering."
                    ),
                    action="Ensure consistent test environment",
                    priority=3,
                    category="environment",
                    confidence=ConfidenceLevel.MEDIUM,
                    tags=["platform", "ios-version", "device"],
                ),
            ],

            FailureCategory.RACE_CONDITION: [
                DebugSuggestion(
                    title="Add synchronization",
                    description=(
                        "Race conditions occur when operations complete in unexpected order. "
                        "Add explicit synchronization points."
                    ),
                    action="Use XCTestExpectation or async/await for synchronization",
                    code_example=(
                        "let expectation = expectation(description: \"Data loaded\")\n"
                        "// ... trigger async operation\n"
                        "wait(for: [expectation], timeout: 5)"
                    ),
                    priority=1,
                    category="sync",
                    confidence=ConfidenceLevel.HIGH,
                    tags=["sync", "expectation", "async"],
                ),
                DebugSuggestion(
                    title="Review shared state",
                    description=(
                        "Race conditions often involve shared mutable state. "
                        "Consider using actors or synchronization primitives."
                    ),
                    action="Identify and protect shared state access",
                    priority=2,
                    category="threading",
                    confidence=ConfidenceLevel.MEDIUM,
                    tags=["actor", "shared", "state"],
                ),
            ],

            FailureCategory.ACCESSIBILITY_MISSING: [
                DebugSuggestion(
                    title="Add accessibility identifier",
                    description=(
                        "The view is missing an accessibility identifier needed for testing. "
                        "Add an identifier to make it testable."
                    ),
                    action="Add .accessibilityIdentifier() to the view",
                    code_example=(
                        "Button(\"Submit\") { action() }\n"
                        "    .accessibilityIdentifier(\"submitButton\")"
                    ),
                    priority=1,
                    category="accessibility",
                    confidence=ConfidenceLevel.HIGH,
                    tags=["identifier", "swiftui", "a11y"],
                ),
                DebugSuggestion(
                    title="Use consistent naming convention",
                    description=(
                        "Follow a consistent naming convention for identifiers "
                        "to make them predictable and maintainable."
                    ),
                    action="Adopt a naming pattern like 'screenName_elementType_purpose'",
                    code_example=".accessibilityIdentifier(\"login_button_submit\")",
                    priority=2,
                    category="convention",
                    confidence=ConfidenceLevel.MEDIUM,
                    tags=["naming", "convention", "pattern"],
                ),
            ],

            FailureCategory.MOCK_FAILURE: [
                DebugSuggestion(
                    title="Verify mock configuration",
                    description=(
                        "The mock may not be configured correctly for this test case. "
                        "Check that all expected calls are stubbed."
                    ),
                    action="Review mock setup and expected interactions",
                    priority=1,
                    category="mock",
                    confidence=ConfidenceLevel.HIGH,
                    tags=["mock", "stub", "configuration"],
                ),
                DebugSuggestion(
                    title="Check mock response data",
                    description=(
                        "The mock response data might not match the expected format. "
                        "Verify the mock returns valid data."
                    ),
                    action="Compare mock response with expected API contract",
                    priority=2,
                    category="data",
                    confidence=ConfidenceLevel.MEDIUM,
                    tags=["response", "data", "contract"],
                ),
            ],
        }

    def get_suggestions(
        self,
        category: FailureCategory,
        limit: int = 5,
    ) -> list[DebugSuggestion]:
        """Get suggestions for a failure category."""
        suggestions = self.knowledge_base.get(category, [])

        # If no specific suggestions, provide generic ones
        if not suggestions:
            suggestions = self._get_generic_suggestions()

        return suggestions[:limit]

    def _get_generic_suggestions(self) -> list[DebugSuggestion]:
        """Get generic debugging suggestions."""
        return [
            DebugSuggestion(
                title="Review test logs",
                description="Check the full test output for additional context about the failure.",
                action="Examine console logs and any attached screenshots",
                priority=1,
                category="debugging",
                confidence=ConfidenceLevel.LOW,
                tags=["logs", "debug", "context"],
            ),
            DebugSuggestion(
                title="Reproduce manually",
                description="Try to reproduce the failure manually to understand the conditions.",
                action="Run the app manually and follow the test steps",
                priority=2,
                category="debugging",
                confidence=ConfidenceLevel.LOW,
                tags=["manual", "reproduce", "debug"],
            ),
            DebugSuggestion(
                title="Check recent changes",
                description="Review recent code changes that might have caused this failure.",
                action="Use git blame or git log to find related changes",
                priority=3,
                category="investigation",
                confidence=ConfidenceLevel.LOW,
                tags=["git", "changes", "history"],
            ),
        ]

    def get_all_suggestions(self) -> list[DebugSuggestion]:
        """Get all suggestions from knowledge base."""
        all_suggestions = []
        for suggestions in self.knowledge_base.values():
            all_suggestions.extend(suggestions)
        return all_suggestions

    def search_suggestions(self, query: str) -> list[DebugSuggestion]:
        """Search suggestions by keyword."""
        query_lower = query.lower()
        matching = []

        for suggestion in self.get_all_suggestions():
            if (
                query_lower in suggestion.title.lower()
                or query_lower in suggestion.description.lower()
                or any(query_lower in tag for tag in suggestion.tags)
            ):
                matching.append(suggestion)

        return matching

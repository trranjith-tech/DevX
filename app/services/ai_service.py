"""
AI analysis service.

`AnalysisEngine` is the abstraction the rest of the app depends on. The only
implementation shipped here, `RuleBasedAnalysisEngine`, is deterministic —
it inspects performance metrics with plain thresholds and never claims to
call an external model. A real LLM-backed engine (e.g. one that calls
OpenAI or the Anthropic API) can be dropped in later by implementing the
same `analyze()` method and swapping the instance created at the bottom of
this file — no controller or router code needs to change.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.enums import IssueType, Severity
from app.exceptions import AIAnalysisException
from app.services.session_service import session_service
from app.store import store

# Thresholds driving the rule-based engine. Kept as module-level constants
# so they're easy to tune without hunting through the analysis logic.
LOW_FPS_THRESHOLD = 30
HIGH_FRAME_DROPS_THRESHOLD = 10
HIGH_CPU_THRESHOLD = 90
HIGH_MEMORY_THRESHOLD = 85
HIGH_TEMPERATURE_THRESHOLD = 45
HIGH_BATTERY_DRAIN_THRESHOLD = 8  # % battery consumed per recorded sample


class AnalysisEngine(ABC):
    @abstractmethod
    def analyze(
        self,
        metrics: list[dict[str, Any]],
        interactions: list[dict[str, Any]],
        screenshots: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Return a list of report dicts with issue_type, severity, root_cause,
        explanation, suggested_fix, confidence_score."""
        raise NotImplementedError


class RuleBasedAnalysisEngine(AnalysisEngine):
    def analyze(
        self,
        metrics: list[dict[str, Any]],
        interactions: list[dict[str, Any]],
        screenshots: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []

        if not metrics:
            findings.append(
                self._finding(
                    IssueType.UNKNOWN,
                    Severity.LOW,
                    "No performance metrics were recorded for this session",
                    "The analysis engine had no metric samples to evaluate, so no "
                    "performance conclusions could be drawn.",
                    "Ensure the mobile SDK is sending performance metrics during the "
                    "recorded session.",
                    confidence=0.3,
                )
            )
            return findings

        avg_fps = sum(m["fps"] for m in metrics) / len(metrics)
        max_frame_drops = max(m["frame_drops"] for m in metrics)
        max_cpu = max(m["cpu_usage"] for m in metrics)
        max_memory = max(m["memory_usage"] for m in metrics)
        max_temperature = max(m["temperature"] for m in metrics)
        max_battery = max(m["battery_usage"] for m in metrics)

        if avg_fps < LOW_FPS_THRESHOLD:
            findings.append(
                self._finding(
                    IssueType.PERFORMANCE,
                    Severity.HIGH,
                    "Low frame rate detected",
                    f"Average FPS across the session was {avg_fps:.1f}, below the "
                    f"{LOW_FPS_THRESHOLD} FPS threshold expected for smooth UI rendering.",
                    "Profile rendering performance and optimize expensive UI operations "
                    "(overdraw, layout thrashing, main-thread work).",
                    confidence=0.92,
                )
            )

        if max_frame_drops > HIGH_FRAME_DROPS_THRESHOLD:
            findings.append(
                self._finding(
                    IssueType.FRAME_DROP,
                    Severity.HIGH,
                    "Excessive frame drops detected",
                    f"A peak of {max_frame_drops} dropped frames was recorded, exceeding "
                    f"the {HIGH_FRAME_DROPS_THRESHOLD}-frame threshold.",
                    "Investigate long-running tasks on the UI thread during the affected "
                    "screens and defer or offload heavy work.",
                    confidence=0.88,
                )
            )

        if max_cpu > HIGH_CPU_THRESHOLD:
            findings.append(
                self._finding(
                    IssueType.CPU,
                    Severity.HIGH,
                    "High CPU utilization detected",
                    f"CPU usage peaked at {max_cpu:.1f}%, above the {HIGH_CPU_THRESHOLD}% "
                    "threshold, indicating heavy computation or inefficient loops.",
                    "Profile CPU hotspots and move non-UI-critical work to background "
                    "threads or coroutines.",
                    confidence=0.85,
                )
            )

        if max_memory > HIGH_MEMORY_THRESHOLD:
            findings.append(
                self._finding(
                    IssueType.MEMORY,
                    Severity.HIGH,
                    "High memory usage detected",
                    f"Memory usage peaked at {max_memory:.1f}%, above the "
                    f"{HIGH_MEMORY_THRESHOLD}% threshold, risking OOM kills on lower-end "
                    "devices.",
                    "Check for memory leaks, large bitmap allocations, and unbounded "
                    "caches.",
                    confidence=0.85,
                )
            )

        if max_temperature > HIGH_TEMPERATURE_THRESHOLD:
            findings.append(
                self._finding(
                    IssueType.TEMPERATURE,
                    Severity.HIGH,
                    "Device thermal threshold exceeded",
                    f"Device temperature peaked at {max_temperature:.1f}\u00b0C, above the "
                    f"{HIGH_TEMPERATURE_THRESHOLD}\u00b0C threshold, which can trigger "
                    "thermal throttling.",
                    "Reduce sustained CPU/GPU load (e.g. rendering complexity, polling "
                    "intervals) during long sessions.",
                    confidence=0.8,
                )
            )

        if max_battery > HIGH_BATTERY_DRAIN_THRESHOLD:
            findings.append(
                self._finding(
                    IssueType.BATTERY,
                    Severity.MEDIUM,
                    "Unusually high battery drain detected",
                    f"Battery usage peaked at {max_battery:.1f}% for a single sample, "
                    f"above the {HIGH_BATTERY_DRAIN_THRESHOLD}% threshold.",
                    "Audit wake locks, background sync frequency, and GPS/sensor usage "
                    "during the session.",
                    confidence=0.75,
                )
            )

        if not findings:
            findings.append(
                self._finding(
                    IssueType.UNKNOWN,
                    Severity.LOW,
                    "No significant issues detected",
                    "All recorded metrics stayed within expected thresholds for this "
                    "session.",
                    "No action required; continue monitoring in future sessions.",
                    confidence=0.6,
                )
            )

        return findings

    @staticmethod
    def _finding(
        issue_type: IssueType,
        severity: Severity,
        root_cause: str,
        explanation: str,
        suggested_fix: str,
        confidence: float,
    ) -> dict[str, Any]:
        return {
            "issue_type": issue_type,
            "severity": severity,
            "root_cause": root_cause,
            "explanation": explanation,
            "suggested_fix": suggested_fix,
            "confidence_score": confidence,
        }


class AIService:
    def __init__(self, engine: AnalysisEngine):
        self._engine = engine

    def analyze(self, session_id: str, user_id: str) -> list[dict[str, Any]]:
        session = session_service.get_by_session_id(session_id, user_id)

        metrics = store.metrics.find_all(lambda m: m["session_id"] == session["session_id"])
        interactions = store.interactions.find_all(lambda i: i["session_id"] == session["session_id"])
        screenshots = store.screenshots.find_all(lambda s: s["session_id"] == session["session_id"])

        try:
            findings = self._engine.analyze(metrics, interactions, screenshots)
        except Exception as exc:  # pragma: no cover - defensive
            raise AIAnalysisException(f"AI analysis failed: {exc}", "AI_ANALYSIS_ERROR") from exc

        reports = []
        now = datetime.now(timezone.utc)
        for finding in findings:
            report = {
                "id": str(uuid4()),
                "session_id": session["session_id"],
                "created_at": now,
                **finding,
            }
            store.ai_reports.create(report)
            reports.append(report)
        return reports

    def get_reports(self, session_id: str, user_id: str) -> list[dict[str, Any]]:
        session_service.get_by_session_id(session_id, user_id)
        reports = store.ai_reports.find_all(lambda r: r["session_id"] == session_id)
        return sorted(reports, key=lambda r: r["created_at"])


# Swap this instance to plug in a real LLM-backed engine later.
ai_service = AIService(engine=RuleBasedAnalysisEngine())

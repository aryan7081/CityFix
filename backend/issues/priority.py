"""
Deterministic priority scoring.

score = w_severity * S + w_supports * U + w_age * A + w_category * C

Maps continuous score to LOW / MEDIUM / HIGH / CRITICAL bands.
Configurable via settings.PRIORITY_WEIGHTS — future evolution: ML ranking,
SLA windows, crew capacity, and city-district budgets.
"""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import Issue

SEVERITY_SCORE = {
    Issue.Severity.MINOR: 0.25,
    Issue.Severity.MODERATE: 0.5,
    Issue.Severity.MAJOR: 0.75,
    Issue.Severity.SEVERE: 1.0,
}

CATEGORY_SCORE = {
    Issue.Category.WATER_LEAK: 1.0,
    Issue.Category.STREETLIGHT: 0.7,
    Issue.Category.POTHOLE: 0.8,
    Issue.Category.GARBAGE: 0.6,
    Issue.Category.OTHER: 0.4,
}


def _support_score(count: int) -> float:
    # Saturating curve: 0 supports → 0, 10+ → ~1
    return min(1.0, count / 10.0)


def _age_score(created_at) -> float:
    # Issues older than 14 days approach 1.0
    age = timezone.now() - created_at
    return min(1.0, age / timedelta(days=14))


def compute_priority_score(issue: Issue) -> float:
    w = settings.PRIORITY_WEIGHTS
    s = SEVERITY_SCORE.get(issue.severity, 0.5)
    u = _support_score(issue.support_count)
    a = _age_score(issue.created_at)
    c = CATEGORY_SCORE.get(issue.category, 0.4)
    return round(
        w["severity"] * s + w["supports"] * u + w["age"] * a + w["category"] * c,
        4,
    )


def score_to_priority(score: float) -> str:
    if score >= 0.75:
        return Issue.Priority.CRITICAL
    if score >= 0.55:
        return Issue.Priority.HIGH
    if score >= 0.35:
        return Issue.Priority.MEDIUM
    return Issue.Priority.LOW


def refresh_priority(issue: Issue, *, save: bool = True) -> Issue:
    issue.priority_score = compute_priority_score(issue)
    issue.priority = score_to_priority(issue.priority_score)
    if save:
        issue.save(update_fields=["priority_score", "priority", "updated_at"])
    return issue

"""
Duplicate detection: geographic proximity + category + text similarity.

Uses Haversine distance (no PostGIS required for MVP) and SequenceMatcher
for description similarity. Scores are deterministic and configurable via settings.
"""

from __future__ import annotations

import hashlib
import logging
import math
from dataclasses import dataclass
from difflib import SequenceMatcher

from django.conf import settings
from django.db.models import QuerySet

from .models import Issue, IssueDuplicate

logger = logging.getLogger("cityfix")

EARTH_RADIUS_M = 6_371_000


@dataclass
class DuplicateCandidate:
    issue: Issue
    score: float
    distance_meters: float
    text_similarity: float


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    rlat1, rlon1, rlat2, rlon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def text_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def draft_fingerprint(category: str, title: str, description: str, lat: float, lng: float) -> str:
    raw = f"{category}|{title}|{description}|{lat:.5f}|{lng:.5f}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _approx_degree_delta(meters: float, latitude: float) -> tuple[float, float]:
    """Bounding box in degrees to prefilter DB rows before Haversine."""
    lat_delta = meters / 111_320
    lng_delta = meters / (111_320 * max(math.cos(math.radians(latitude)), 0.01))
    return lat_delta, lng_delta


def _open_issues_queryset() -> QuerySet[Issue]:
    closed = {Issue.Status.RESOLVED, Issue.Status.REJECTED}
    return Issue.objects.exclude(status__in=closed).select_related("reporter")


def find_duplicates(
    *,
    category: str,
    title: str,
    description: str,
    latitude: float,
    longitude: float,
    exclude_issue_id: int | None = None,
    limit: int = 5,
) -> list[DuplicateCandidate]:
    max_distance = settings.DUPLICATE_DISTANCE_METERS
    min_text = settings.DUPLICATE_TEXT_SIMILARITY
    min_score = settings.DUPLICATE_MIN_SCORE

    lat_delta, lng_delta = _approx_degree_delta(max_distance * 1.5, latitude)
    qs = _open_issues_queryset().filter(
        category=category,
        latitude__gte=latitude - lat_delta,
        latitude__lte=latitude + lat_delta,
        longitude__gte=longitude - lng_delta,
        longitude__lte=longitude + lng_delta,
    )
    if exclude_issue_id:
        qs = qs.exclude(pk=exclude_issue_id)

    combined_text = f"{title} {description}"
    candidates: list[DuplicateCandidate] = []

    for issue in qs[:100]:
        dist = haversine_meters(
            latitude,
            longitude,
            float(issue.latitude),
            float(issue.longitude),
        )
        if dist > max_distance:
            continue

        sim = text_similarity(combined_text, f"{issue.title} {issue.description}")
        # Geographic score: 1.0 at same point, 0.0 at max_distance
        geo_score = max(0.0, 1.0 - (dist / max_distance))
        # Require either strong text match or very close proximity
        if sim < min_text and geo_score < 0.85:
            continue

        # Weighted composite: proximity and text; category already matched
        score = 0.45 * geo_score + 0.55 * sim
        if score >= min_score:
            candidates.append(
                DuplicateCandidate(
                    issue=issue,
                    score=round(score, 4),
                    distance_meters=round(dist, 2),
                    text_similarity=round(sim, 4),
                )
            )

    candidates.sort(key=lambda c: c.score, reverse=True)
    logger.info(
        "Duplicate scan category=%s lat=%.5f lng=%.5f found=%d",
        category,
        latitude,
        longitude,
        len(candidates),
    )
    return candidates[:limit]


def persist_candidates(
    candidates: list[DuplicateCandidate],
    *,
    source_issue: Issue | None = None,
    fingerprint: str = "",
) -> list[IssueDuplicate]:
    records = []
    for c in candidates:
        records.append(
            IssueDuplicate.objects.create(
                source_issue=source_issue,
                target_issue=c.issue,
                score=c.score,
                distance_meters=c.distance_meters,
                text_similarity=c.text_similarity,
                relation=IssueDuplicate.Relation.CANDIDATE,
                draft_fingerprint=fingerprint,
            )
        )
    return records

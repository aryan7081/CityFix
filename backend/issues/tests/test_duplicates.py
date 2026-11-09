from django.contrib.auth import get_user_model
from django.test import TestCase

from issues.duplicates import find_duplicates, haversine_meters, text_similarity
from issues.models import Issue

User = get_user_model()


class DuplicateDetectionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="c1", password="pass", role="CITIZEN")
        self.issue = Issue.objects.create(
            title="Large pothole on MG Road",
            description="Deep pothole near the bus stop on MG Road causing traffic issues",
            category=Issue.Category.POTHOLE,
            latitude="12.971600",
            longitude="77.594600",
            address="MG Road",
            reporter=self.user,
        )

    def test_haversine_same_point(self):
        self.assertAlmostEqual(haversine_meters(12.97, 77.59, 12.97, 77.59), 0, places=1)

    def test_text_similarity_high_for_near_duplicates(self):
        sim = text_similarity(
            "Large pothole on MG Road near bus stop",
            "Deep pothole near the bus stop on MG Road causing traffic issues",
        )
        self.assertGreater(sim, 0.3)

    def test_find_duplicates_nearby_same_category(self):
        candidates = find_duplicates(
            category="POTHOLE",
            title="Pothole on MG Road by bus stop",
            description="There is a deep pothole near the bus stop on MG Road",
            latitude=12.97165,
            longitude=77.59455,
        )
        self.assertTrue(any(c.issue.id == self.issue.id for c in candidates))

    def test_different_category_not_matched(self):
        candidates = find_duplicates(
            category="GARBAGE",
            title="Large pothole on MG Road",
            description="Deep pothole near the bus stop on MG Road causing traffic issues",
            latitude=12.97165,
            longitude=77.59455,
        )
        self.assertEqual(candidates, [])

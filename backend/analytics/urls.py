from django.urls import path

from .views import DashboardStatsView, InvalidateCacheView, PublicStatsView, SystemHealthView

urlpatterns = [
    path("dashboard/", DashboardStatsView.as_view(), name="analytics-dashboard"),
    path("public/", PublicStatsView.as_view(), name="analytics-public"),
    path("cache/invalidate/", InvalidateCacheView.as_view(), name="analytics-cache-invalidate"),
    path("system-health/", SystemHealthView.as_view(), name="analytics-system-health"),
]

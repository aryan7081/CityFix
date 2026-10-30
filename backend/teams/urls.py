from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MaintenanceTeamViewSet

router = DefaultRouter()
router.register("", MaintenanceTeamViewSet, basename="teams")

urlpatterns = [
    path("", include(router.urls)),
]

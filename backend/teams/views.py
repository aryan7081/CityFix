from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from common.permissions import IsAdminRole

from .models import MaintenanceTeam
from .serializers import MaintenanceTeamSerializer


class MaintenanceTeamViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceTeam.objects.prefetch_related("members").all()
    serializer_class = MaintenanceTeamSerializer
    filterset_fields = ["is_active", "specialization"]
    search_fields = ["name", "description"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAdminRole()]

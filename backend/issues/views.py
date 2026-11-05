from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdminOrMaintenance, IsAdminRole, IsCitizenRole
from teams.models import MaintenanceTeam

from .models import Issue, IssueDuplicate
from .serializers import (
    AssignSerializer,
    DuplicateCheckSerializer,
    IssueCreateSerializer,
    IssueDetailSerializer,
    IssueDuplicateSerializer,
    IssueListSerializer,
    PrioritySerializer,
    ResolveSerializer,
    SupportSerializer,
    TransitionSerializer,
)
from . import services


class IssueListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "status", "priority", "severity"]
    search_fields = ["title", "description", "address"]
    ordering_fields = ["created_at", "priority_score", "support_count", "updated_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return IssueCreateSerializer
        return IssueListSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Issue.objects.select_related("reporter", "assigned_team")
        if user.role == "CITIZEN":
            return qs.filter(reporter=user)
        if user.role == "MAINTENANCE":
            team_ids = user.maintenance_teams.values_list("id", flat=True)
            return qs.filter(assigned_team_id__in=team_ids)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = IssueCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        image = data.pop("image", None)
        force = data.pop("force", False)

        issue, suggestions = services.create_issue(
            reporter=request.user,
            data=data,
            image=image,
            force=force,
        )
        if issue is None:
            return Response(
                {
                    "success": False,
                    "duplicate_suggestions": suggestions,
                    "message": (
                        "Possible duplicate issues found. "
                        "Support an existing report or resubmit with force=true."
                    ),
                },
                status=status.HTTP_409_CONFLICT,
            )
        return Response(
            {
                "success": True,
                "issue": IssueDetailSerializer(issue, context={"request": request}).data,
                "duplicate_suggestions": suggestions,
            },
            status=status.HTTP_201_CREATED,
        )


class IssueDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = IssueDetailSerializer
    lookup_field = "public_id"

    def get_queryset(self):
        return Issue.objects.select_related("reporter", "assigned_team").prefetch_related(
            "images", "status_history__actor"
        )


class DuplicateCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DuplicateCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        suggestions = services.check_duplicates_for_draft(serializer.validated_data)
        return Response({"suggestions": suggestions})


class SupportIssueView(APIView):
    permission_classes = [IsAuthenticated, IsCitizenRole]

    def post(self, request, public_id):
        issue = get_object_or_404(Issue, public_id=public_id)
        serializer = SupportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        support = services.support_issue(
            issue=issue,
            user=request.user,
            note=serializer.validated_data.get("note", ""),
        )
        return Response(
            {
                "success": True,
                "support_count": issue.support_count,
                "created_at": support.created_at,
            },
            status=status.HTTP_201_CREATED,
        )


class TransitionIssueView(APIView):
    permission_classes = [IsAdminOrMaintenance]

    def post(self, request, public_id):
        issue = get_object_or_404(Issue, public_id=public_id)
        serializer = TransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Maintenance may only move ASSIGNED → IN_PROGRESS or IN_PROGRESS → RESOLVED
        # (resolve has its own endpoint; allow IN_PROGRESS here for progress updates)
        if request.user.role == "MAINTENANCE":
            allowed = {
                "IN_PROGRESS",
            }
            if serializer.validated_data["status"] not in allowed:
                return Response(
                    {"detail": "Maintenance staff should use accept/resolve endpoints."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        issue = services.transition_issue(
            issue=issue,
            new_status=serializer.validated_data["status"],
            actor=request.user,
            comment=serializer.validated_data.get("comment", ""),
        )
        return Response(IssueDetailSerializer(issue, context={"request": request}).data)


class AssignIssueView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, public_id):
        issue = get_object_or_404(Issue, public_id=public_id)
        serializer = AssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team = get_object_or_404(MaintenanceTeam, pk=serializer.validated_data["team_id"])
        assignment = services.assign_team(
            issue=issue,
            team=team,
            actor=request.user,
            notes=serializer.validated_data.get("notes", ""),
        )
        issue.refresh_from_db()
        return Response(
            {
                "success": True,
                "assignment_id": assignment.id,
                "issue": IssueDetailSerializer(issue, context={"request": request}).data,
            }
        )


class AcceptAssignmentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, public_id):
        issue = get_object_or_404(Issue, public_id=public_id)
        assignment = services.accept_assignment(issue=issue, user=request.user)
        issue.refresh_from_db()
        return Response(
            {
                "success": True,
                "accepted_at": assignment.accepted_at,
                "issue": IssueDetailSerializer(issue, context={"request": request}).data,
            }
        )


class ResolveIssueView(APIView):
    permission_classes = [IsAdminOrMaintenance]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, public_id):
        issue = get_object_or_404(Issue, public_id=public_id)
        serializer = ResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        issue = services.resolve_issue(
            issue=issue,
            user=request.user,
            notes=serializer.validated_data.get("notes", ""),
            image=serializer.validated_data.get("image"),
        )
        return Response(IssueDetailSerializer(issue, context={"request": request}).data)


class SetPriorityView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, public_id):
        issue = get_object_or_404(Issue, public_id=public_id)
        serializer = PrioritySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        issue = services.set_priority_manual(
            issue=issue,
            priority=serializer.validated_data["priority"],
            actor=request.user,
        )
        return Response(IssueDetailSerializer(issue, context={"request": request}).data)


class DuplicateListView(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = IssueDuplicateSerializer
    queryset = IssueDuplicate.objects.select_related("target_issue").order_by("-detected_at")

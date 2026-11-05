from django.urls import path

from .views import (
    AcceptAssignmentView,
    AssignIssueView,
    DuplicateCheckView,
    DuplicateListView,
    IssueDetailView,
    IssueListCreateView,
    ResolveIssueView,
    SetPriorityView,
    SupportIssueView,
    TransitionIssueView,
)

urlpatterns = [
    path("", IssueListCreateView.as_view(), name="issue-list-create"),
    path("duplicates/check/", DuplicateCheckView.as_view(), name="issue-duplicate-check"),
    path("duplicates/", DuplicateListView.as_view(), name="issue-duplicate-list"),
    path("<uuid:public_id>/", IssueDetailView.as_view(), name="issue-detail"),
    path("<uuid:public_id>/support/", SupportIssueView.as_view(), name="issue-support"),
    path("<uuid:public_id>/transition/", TransitionIssueView.as_view(), name="issue-transition"),
    path("<uuid:public_id>/assign/", AssignIssueView.as_view(), name="issue-assign"),
    path("<uuid:public_id>/accept/", AcceptAssignmentView.as_view(), name="issue-accept"),
    path("<uuid:public_id>/resolve/", ResolveIssueView.as_view(), name="issue-resolve"),
    path("<uuid:public_id>/priority/", SetPriorityView.as_view(), name="issue-priority"),
]

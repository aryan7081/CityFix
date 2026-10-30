from django.contrib import admin

from .models import MaintenanceTeam, TeamAssignment


@admin.register(MaintenanceTeam)
class MaintenanceTeamAdmin(admin.ModelAdmin):
    list_display = ("name", "specialization", "is_active")
    filter_horizontal = ("members",)


@admin.register(TeamAssignment)
class TeamAssignmentAdmin(admin.ModelAdmin):
    list_display = ("issue", "team", "is_active", "assigned_at")
    list_filter = ("is_active",)

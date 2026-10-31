from django.contrib import admin

from .models import Issue, IssueDuplicate, IssueImage, IssueStatusHistory, IssueSupport


class IssueImageInline(admin.TabularInline):
    model = IssueImage
    extra = 0


class StatusHistoryInline(admin.TabularInline):
    model = IssueStatusHistory
    extra = 0
    readonly_fields = ("previous_status", "new_status", "actor", "comment", "created_at")


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "title",
        "category",
        "status",
        "priority",
        "support_count",
        "reporter",
        "created_at",
    )
    list_filter = ("status", "priority", "category")
    search_fields = ("title", "description", "address", "public_id")
    inlines = [IssueImageInline, StatusHistoryInline]


@admin.register(IssueSupport)
class IssueSupportAdmin(admin.ModelAdmin):
    list_display = ("issue", "user", "created_at")


@admin.register(IssueDuplicate)
class IssueDuplicateAdmin(admin.ModelAdmin):
    list_display = ("target_issue", "score", "relation", "detected_at")

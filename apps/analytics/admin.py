"""Read-only admin for visitor statistics (data is written only by the middleware)."""

from django.contrib import admin

from .models import CvDownloadStat, DailyVisitor, PageViewStat


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DailyVisitor)
class DailyVisitorAdmin(ReadOnlyAdmin):
    list_display = ("date", "short_id", "views", "first_page", "referrer", "first_seen", "last_seen")
    list_filter = ("date",)
    search_fields = ("first_page", "referrer")
    date_hierarchy = "date"

    @admin.display(description="Visitor")
    def short_id(self, obj):
        return obj.visitor[:10] + "…"


@admin.register(PageViewStat)
class PageViewStatAdmin(ReadOnlyAdmin):
    list_display = ("date", "path", "views")
    list_filter = ("date",)
    search_fields = ("path",)
    date_hierarchy = "date"


@admin.register(CvDownloadStat)
class CvDownloadStatAdmin(ReadOnlyAdmin):
    list_display = ("date", "downloads")
    date_hierarchy = "date"

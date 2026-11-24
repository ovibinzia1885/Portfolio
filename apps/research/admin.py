from django.contrib import admin

from .models import Research


@admin.register(Research)
class ResearchAdmin(admin.ModelAdmin):
    list_display = ("title", "publication_type", "indexing", "venue", "publication_date", "display_order")
    list_editable = ("display_order",)
    list_filter = ("publication_type", "indexing", "publication_date")
    search_fields = ("title", "authors", "venue", "doi")
    ordering = ("display_order", "-publication_date")
    readonly_fields = ("created_at", "updated_at")

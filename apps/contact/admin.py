from django.contrib import admin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "is_read", "created_at")
    list_editable = ("is_read",)
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "email", "subject", "message")
    ordering = ("-created_at",)
    # Visitor messages are evidence: read / mark as read / delete, never edit or fake.
    readonly_fields = ("name", "email", "subject", "message", "created_at", "updated_at")

    def has_add_permission(self, request):
        return False

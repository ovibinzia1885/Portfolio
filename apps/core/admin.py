from django.contrib import admin

from .admin_mixins import ImagePreviewMixin
from django import forms

from .cloudinary_url import is_valid, masked_shape, normalize_cloudinary_url
from .models import Profile, SiteSection, SiteSetting


class SiteSettingForm(forms.ModelForm):
    cloudinary_url = forms.CharField(
        label="Cloudinary connection", required=False, widget=forms.PasswordInput(render_value=False),
        help_text="Paste cloudinary://API_KEY:API_SECRET@CLOUD_NAME (Cloudinary > Settings > API Keys). "
                  "Leave empty to keep the saved value. Hidden after saving.",
    )
    clear_cloudinary = forms.BooleanField(label="Remove the saved Cloudinary connection", required=False)

    class Meta:
        model = SiteSetting
        fields = ("cloudinary_url",)

    def clean_cloudinary_url(self):
        value = self.cleaned_data.get("cloudinary_url", "")
        if not value:
            return self.instance.cloudinary_url  # keep what is saved
        normalized = normalize_cloudinary_url(value)
        if not is_valid(normalized):
            raise forms.ValidationError(
                f"Not a Cloudinary connection (shape: {masked_shape(normalized)}). "
                "Expected cloudinary://API_KEY:API_SECRET@CLOUD_NAME."
            )
        return normalized

    def save(self, commit=True):
        if self.cleaned_data.get("clear_cloudinary"):
            self.instance.cloudinary_url = ""
        return super().save(commit)


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    form = SiteSettingForm
    list_display = ("__str__", "cloudinary_status", "updated_at")
    readonly_fields = ("cloudinary_status",)
    fields = ("cloudinary_status", "cloudinary_url", "clear_cloudinary")

    @admin.display(description="Cloudinary")
    def cloudinary_status(self, obj):
        if obj and is_valid(obj.cloudinary_url):
            return f"Connected (cloud: {obj.cloudinary_url.rsplit('@', 1)[-1]})"
        return "Not set"

    def has_add_permission(self, request):
        return super().has_add_permission(request) and not SiteSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Profile)
class ProfileAdmin(ImagePreviewMixin, admin.ModelAdmin):
    preview_field = "photo"
    list_display = ("full_name", "headline", "email", "image_preview")
    search_fields = ("full_name", "headline", "email")
    readonly_fields = ("image_preview", "created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("full_name", "headline", "short_intro", "bio", "photo", "image_preview")}),
        ("Hero & availability", {"fields": ("hero_greeting", "hero_button_label", "is_available", "availability_text")}),
        ("Contact", {"fields": ("email", "phone", "location")}),
        ("CV", {"fields": ("resume",)}),
        ("Links", {"fields": ("github_url", "linkedin_url", "google_scholar_url", "facebook_url", "twitter_url")}),
        ("Website", {"fields": ("show_visitor_count", "created_at", "updated_at")}),
    )

    def has_add_permission(self, request):
        # The website shows a single profile: once it exists, edit it instead of adding another.
        return super().has_add_permission(request) and not Profile.objects.exists()


@admin.register(SiteSection)
class SiteSectionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "title", "display_order", "is_visible")
    list_editable = ("display_order", "is_visible")
    readonly_fields = ("key",)
    fieldsets = (
        (None, {"fields": ("key", "is_visible", "display_order", "label", "icon")}),
        ("Home page", {"fields": ("eyebrow", "title", "subtitle")}),
        ("Own page", {"fields": ("page_title", "page_subtitle"),
                      "description": "Only for sections with their own page: Projects, Certifications, Blog, Research, Contact."}),
    )

    # The list of sections is fixed by the website; they can be edited or hidden, not added or deleted.
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

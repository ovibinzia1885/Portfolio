from django.contrib import admin

from .models import Skill, SkillSubcategory


@admin.register(SkillSubcategory)
class SkillSubcategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "main_category", "display_order")
    list_editable = ("display_order",)
    list_filter = ("main_category",)
    search_fields = ("name",)
    ordering = ("main_category", "display_order", "name")


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = (
        "name", "main_category", "subcategory", "experience_level", "display_order",
    )
    list_editable = ("display_order",)
    list_filter = ("main_category", "subcategory", "experience_level")
    search_fields = ("name", "subcategory__name")
    list_select_related = ("subcategory",)
    ordering = ("main_category", "subcategory__display_order", "display_order", "name")

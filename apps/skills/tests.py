from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from apps.core.testing import AdminClientMixin
from apps.core.views import group_skills

from .models import MainCategory, Skill, SkillSubcategory

T, PM, SOFT = MainCategory.TECHNICAL, MainCategory.PROJECT_MANAGEMENT, MainCategory.SOFT


class SkillModelTests(TestCase):
    def setUp(self):
        self.auto = SkillSubcategory.objects.create(main_category=T, name="QA Sub Automation", display_order=1)
        self.agile = SkillSubcategory.objects.create(main_category=PM, name="QA Sub Agile", display_order=1)

    def test_subcategory_must_match_main_category(self):
        skill = Skill(name="Scrum", main_category=T, subcategory=self.agile)
        with self.assertRaises(ValidationError):
            skill.full_clean()
        Skill(name="Scrum", main_category=PM, subcategory=self.agile).full_clean()

    def test_subcategory_unique_per_main_category(self):
        with self.assertRaises(IntegrityError):
            SkillSubcategory.objects.create(main_category=T, name="QA Sub Automation")

    def test_grouping_skips_empty_categories(self):
        Skill.objects.create(name="Playwright", main_category=T, subcategory=self.auto)
        Skill.objects.create(name="Communication", main_category=SOFT)
        groups = group_skills()
        self.assertEqual([g["key"] for g in groups], [T, SOFT])  # PM has no skills
        self.assertEqual(groups[0]["subgroups"][0]["name"], "QA Sub Automation")
        self.assertEqual(groups[1]["subgroups"][0]["name"], "General")

    def test_homepage_shows_skills(self):
        Skill.objects.create(name="Playwright", main_category=T, subcategory=self.auto)
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "Playwright")
        self.assertContains(response, "QA Sub Automation")


class SkillAdminTests(AdminClientMixin, TestCase):
    def test_crud_search_and_filter(self):
        sub = SkillSubcategory.objects.create(main_category=T, name="QA Sub API")
        add = reverse("admin:skills_skill_add")
        data = {"name": "Postman", "main_category": T, "subcategory": sub.pk,
                "experience_level": "advanced", "display_order": "0"}
        self.assertEqual(self.client.post(add, data).status_code, 302)
        skill = Skill.objects.get(name="Postman")

        changelist = reverse("admin:skills_skill_changelist")
        self.assertContains(self.client.get(changelist, {"q": "API"}), "Postman")  # search by subcategory
        self.assertContains(self.client.get(changelist, {"main_category__exact": T}), "Postman")

        self.client.post(reverse("admin:skills_skill_change", args=[skill.pk]), {**data, "experience_level": "expert"})
        skill.refresh_from_db()
        self.assertEqual(skill.experience_level, "expert")

        self.client.post(reverse("admin:skills_skill_delete", args=[skill.pk]), {"post": "yes"})
        self.assertFalse(Skill.objects.exists())

    def test_wrong_subcategory_rejected_in_admin(self):
        sub = SkillSubcategory.objects.create(main_category=PM, name="QA Sub Agile")
        data = {"name": "Selenium", "main_category": T, "subcategory": sub.pk,
                "experience_level": "advanced", "display_order": "0"}
        response = self.client.post(reverse("admin:skills_skill_add"), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Skill.objects.exists())

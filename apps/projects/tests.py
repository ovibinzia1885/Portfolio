from django.test import TestCase
from django.urls import resolve, reverse
from PIL import Image

from apps.core.testing import AdminClientMixin, TempMediaMixin, png_upload

from .models import Project, ProjectImage, ProjectType
from .views import ProjectDetailView, collect_technologies


class ProjectModelTests(TempMediaMixin, TestCase):
    def test_slug_is_unique_and_unicode(self):
        a = Project.objects.create(title="Daraz Web Automation", summary="s")
        b = Project.objects.create(title="Daraz Web Automation", summary="s")
        bn = Project.objects.create(title="বাংলা প্রজেক্ট", summary="s")
        self.assertEqual(a.slug, "daraz-web-automation")
        self.assertNotEqual(a.slug, b.slug)
        self.assertTrue(bn.slug)
        self.assertEqual(self.client.get(bn.get_absolute_url()).status_code, 200)

    def test_technologies_and_cover(self):
        project = Project.objects.create(title="P", summary="s", technologies="Playwright, ,JavaScript ")
        self.assertEqual(project.technology_list, ["Playwright", "JavaScript"])
        self.assertIsNone(project.cover_image)
        second = ProjectImage.objects.create(project=project, image=png_upload("b.png"), display_order=2)
        first = ProjectImage.objects.create(project=project, image=png_upload("a.png"), display_order=1)
        self.assertEqual(project.cover_image, first)
        self.assertNotEqual(project.cover_image, second)

    def test_collect_technologies_is_case_insensitive(self):
        p1 = Project(title="a", technologies="SQL, Playwright")
        p2 = Project(title="b", technologies="sql, Jira")
        self.assertEqual([k for k, _ in collect_technologies([p1, p2])], ["jira", "playwright", "sql"])

    def test_large_upload_is_resized(self):
        project = Project.objects.create(title="Big", summary="s")
        image = ProjectImage.objects.create(project=project, image=png_upload("big.png", size=(3000, 1500)))
        with Image.open(image.image.path) as stored:
            self.assertEqual(stored.size, (1920, 960))

    def test_small_upload_is_untouched(self):
        project = Project.objects.create(title="Small", summary="s")
        image = ProjectImage.objects.create(project=project, image=png_upload("s.png", size=(800, 600)))
        with Image.open(image.image.path) as stored:
            self.assertEqual(stored.size, (800, 600))


class ProjectViewTests(TempMediaMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client_project = Project.objects.create(
            title="PDM Enterprise", summary="ERP automation", project_type=ProjectType.CLIENT,
            technologies="Playwright, MySQL", is_featured=True, display_order=1,
            repository_url="https://github.com/example/pdm", live_url="https://example.com/pdm")
        cls.personal = Project.objects.create(
            title="Daraz Web Automation", summary="Cross-browser UI tests",
            project_type=ProjectType.PERSONAL, technologies="Playwright", display_order=2)

    def test_url_resolves(self):
        match = resolve(f"/projects/{self.personal.slug}/")
        self.assertEqual(match.func.view_class, ProjectDetailView)
        self.assertEqual(reverse("projects:list"), "/projects/")

    def test_list_groups_and_filter_buttons(self):
        response = self.client.get(reverse("projects:list"))
        groups = {g["key"]: g for g in response.context["project_groups"]}
        self.assertEqual(groups[ProjectType.CLIENT]["projects"], [self.client_project])
        self.assertEqual(groups[ProjectType.PERSONAL]["projects"], [self.personal])
        self.assertContains(response, 'data-filter="mysql"')

    def test_detail_shows_links_and_other_projects(self):
        response = self.client.get(self.client_project.get_absolute_url())
        self.assertContains(response, "https://github.com/example/pdm")
        self.assertContains(response, "https://example.com/pdm")
        self.assertIn(self.personal, list(response.context["other_projects"]))
        self.assertContains(response, '<link rel="canonical" href="http://testserver/projects/pdm-enterprise/">', html=False)

    def test_only_featured_on_homepage(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "PDM Enterprise")
        self.assertNotContains(response, "Daraz Web Automation")

    def test_unknown_slug_404(self):
        self.assertEqual(self.client.get("/projects/does-not-exist/").status_code, 404)


class ProjectAdminTests(TempMediaMixin, AdminClientMixin, TestCase):
    def inline(self, total=1, **forms):
        data = {"images-TOTAL_FORMS": str(total), "images-INITIAL_FORMS": "0",
                "images-MIN_NUM_FORMS": "0", "images-MAX_NUM_FORMS": "1000"}
        data.update(forms)
        return data

    def test_add_project_with_multiple_images(self):
        data = {"project_type": "client", "title": "Erasta SPARKASSE", "slug": "",
                "summary": "Banking QA", "technologies": "Postman", "display_order": "0",
                **self.inline(2, **{"images-0-image": png_upload("one.png"), "images-0-display_order": "0",
                                    "images-1-image": png_upload("two.png"), "images-1-display_order": "1"})}
        response = self.client.post(reverse("admin:projects_project_add"), data)
        self.assertEqual(response.status_code, 302, getattr(response, "context", None) and response.context.get("errors"))
        project = Project.objects.get(title="Erasta SPARKASSE")
        self.assertEqual(project.images.count(), 2)
        self.assertEqual(project.slug, "erasta-sparkasse")

        changelist = self.client.get(reverse("admin:projects_project_changelist"), {"q": "Banking"})
        self.assertContains(changelist, "Erasta SPARKASSE")
        self.assertContains(self.client.get(reverse("admin:projects_project_changelist"),
                                            {"project_type__exact": "client"}), "Erasta")

    def test_delete_project_removes_images(self):
        project = Project.objects.create(title="X", summary="s")
        ProjectImage.objects.create(project=project, image=png_upload())
        self.client.post(reverse("admin:projects_project_delete", args=[project.pk]), {"post": "yes"})
        self.assertFalse(ProjectImage.objects.exists())

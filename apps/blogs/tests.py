from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.core.testing import AdminClientMixin, TempMediaMixin, png_upload

from .models import BlogCategory, BlogPost, BlogTag

PUBLISHED = BlogPost.Status.PUBLISHED


class BlogModelTests(TestCase):
    def test_publish_sets_date_and_slug(self):
        post = BlogPost.objects.create(title="Playwright Tips", content="x", status=PUBLISHED)
        self.assertIsNotNone(post.published_at)
        self.assertEqual(post.slug, "playwright-tips")
        draft = BlogPost.objects.create(title="Draft", content="x")
        self.assertIsNone(draft.published_at)

    def test_reading_time(self):
        self.assertEqual(BlogPost(content="word " * 50).reading_time, 1)
        self.assertEqual(BlogPost(content="word " * 1000).reading_time, 5)

    def test_published_queryset_hides_drafts_and_future(self):
        live = BlogPost.objects.create(title="Live", content="x", status=PUBLISHED)
        BlogPost.objects.create(title="Draft", content="x")
        BlogPost.objects.create(title="Future", content="x", status=PUBLISHED,
                                published_at=timezone.now() + timedelta(days=3))
        self.assertEqual(list(BlogPost.objects.published()), [live])

    def test_category_and_tag_urls(self):
        cat = BlogCategory.objects.create(name="Test Automation")
        tag = BlogTag.objects.create(name="playwright")
        self.assertEqual(cat.get_absolute_url(), "/blog/category/test-automation/")
        self.assertEqual(tag.get_absolute_url(), "/blog/tag/playwright/")


class BlogViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cat = BlogCategory.objects.create(name="QA")
        cls.other_cat = BlogCategory.objects.create(name="Django")
        cls.tag = BlogTag.objects.create(name="api")
        for i in range(8):
            post = BlogPost.objects.create(
                title=f"Post {i}", content=f"Body {i} about testing", excerpt=f"Excerpt {i}",
                status=PUBLISHED, category=cls.cat if i % 2 else cls.other_cat,
                published_at=timezone.now() - timedelta(days=i))
            if i < 3:
                post.tags.add(cls.tag)
        cls.unique = BlogPost.objects.create(title="Newman CLI guide", content="Run collections",
                                             status=PUBLISHED, published_at=timezone.now() - timedelta(days=20))

    def test_pagination(self):
        first = self.client.get(reverse("blogs:list"))
        self.assertEqual(len(first.context["posts"]), 6)
        self.assertEqual(first.context["page_obj"].paginator.num_pages, 2)
        second = self.client.get(reverse("blogs:list"), {"page": 2})
        self.assertEqual(len(second.context["posts"]), 3)
        self.assertContains(second, '<link rel="canonical" href="http://testserver/blog/?page=2">', html=False)
        self.assertEqual(self.client.get(reverse("blogs:list"), {"page": 99}).status_code, 404)

    def test_search(self):
        response = self.client.get(reverse("blogs:list"), {"q": "newman"})
        self.assertEqual(list(response.context["posts"]), [self.unique])
        self.assertContains(response, "noindex, follow")  # search result pages are not indexed
        empty = self.client.get(reverse("blogs:list"), {"q": "zzzz-nothing"})
        self.assertEqual(len(empty.context["posts"]), 0)

    def test_category_and_tag_filters(self):
        by_cat = self.client.get(self.cat.get_absolute_url())
        self.assertEqual(by_cat.context["page_obj"].paginator.count, 4)
        by_tag = self.client.get(self.tag.get_absolute_url())
        self.assertEqual(by_tag.context["page_obj"].paginator.count, 3)
        self.assertEqual(self.client.get("/blog/category/unknown/").status_code, 404)

    def test_detail_meta_and_related(self):
        post = BlogPost.objects.get(title="Post 1")
        response = self.client.get(post.get_absolute_url())
        self.assertContains(response, '<meta property="og:type" content="article">', html=False)
        self.assertContains(response, '<meta name="description" content="Excerpt 1">', html=False)
        self.assertTrue(all(p.category == self.cat for p in response.context["related_posts"]))

    def test_content_is_html_escaped(self):
        post = BlogPost.objects.create(title="XSS", content="<script>alert(1)</script>", status=PUBLISHED)
        response = self.client.get(post.get_absolute_url())
        self.assertNotContains(response, "<script>alert(1)</script>")
        self.assertContains(response, "&lt;script&gt;")


class BlogAdminTests(TempMediaMixin, AdminClientMixin, TestCase):
    def test_add_update_delete_with_cover_and_tags(self):
        cat = BlogCategory.objects.create(name="QA")
        tag = BlogTag.objects.create(name="api")
        data = {"title": "Admin post", "slug": "", "excerpt": "e", "content": "Hello world",
                "status": PUBLISHED, "category": cat.pk, "tags": [tag.pk],
                "cover_image": png_upload("cover.png")}
        response = self.client.post(reverse("admin:blogs_blogpost_add"), data)
        self.assertEqual(response.status_code, 302)
        post = BlogPost.objects.get(title="Admin post")
        self.assertTrue(post.cover_image)
        self.assertEqual(list(post.tags.all()), [tag])
        self.assertEqual(self.client.get(post.get_absolute_url()).status_code, 200)

        changelist = reverse("admin:blogs_blogpost_changelist")
        self.assertContains(self.client.get(changelist, {"q": "Hello"}), "Admin post")
        self.assertContains(self.client.get(changelist, {"status__exact": PUBLISHED}), "Admin post")

        data.pop("cover_image")
        self.client.post(reverse("admin:blogs_blogpost_change", args=[post.pk]), {**data, "status": "draft"})
        post.refresh_from_db()
        self.assertEqual(post.status, "draft")
        self.assertEqual(self.client.get(post.get_absolute_url()).status_code, 404)

        self.client.post(reverse("admin:blogs_blogpost_delete", args=[post.pk]), {"post": "yes"})
        self.assertFalse(BlogPost.objects.exists())

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import DetailView, ListView

from .models import BlogCategory, BlogPost, BlogTag


def published_filter():
    """Posts that are live now (scheduled posts with a future date are not counted yet)."""
    return Q(posts__status=BlogPost.Status.PUBLISHED, posts__published_at__lte=timezone.now())


class BlogListView(ListView):
    """Blog listing with search, category/tag filtering and pagination."""

    template_name = "blogs/list.html"
    context_object_name = "posts"
    paginate_by = 6

    def get_queryset(self):
        queryset = (
            BlogPost.objects.published()
            .select_related("category")
            .prefetch_related("tags")
        )
        self.category = None
        self.tag = None
        if slug := self.kwargs.get("category_slug"):
            self.category = get_object_or_404(BlogCategory, slug=slug)
            queryset = queryset.filter(category=self.category)
        if slug := self.kwargs.get("tag_slug"):
            self.tag = get_object_or_404(BlogTag, slug=slug)
            queryset = queryset.filter(tags=self.tag)
        self.query = self.request.GET.get("q", "").strip()
        if self.query:
            queryset = queryset.filter(
                Q(title__icontains=self.query)
                | Q(excerpt__icontains=self.query)
                | Q(content__icontains=self.query)
            ).distinct()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        live = published_filter()
        context.update(
            query=self.query,
            active_category=self.category,
            active_tag=self.tag,
            categories=BlogCategory.objects.annotate(
                post_count=Count("posts", filter=live)
            ).filter(post_count__gt=0),
            tags=BlogTag.objects.annotate(
                post_count=Count("posts", filter=live)
            ).filter(post_count__gt=0),
        )
        return context


class BlogDetailView(DetailView):
    template_name = "blogs/detail.html"
    context_object_name = "post"

    def get_queryset(self):
        return (
            BlogPost.objects.published()
            .select_related("category")
            .prefetch_related("tags")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object
        related = BlogPost.objects.published().exclude(pk=post.pk)
        if post.category_id:
            related = related.filter(category=post.category)
        context["related_posts"] = related.select_related("category").prefetch_related("tags")[:3]
        return context

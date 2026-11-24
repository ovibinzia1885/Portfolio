from django.urls import path

from . import views

app_name = "blogs"

urlpatterns = [
    path("", views.BlogListView.as_view(), name="list"),
    path("category/<str:category_slug>/", views.BlogListView.as_view(), name="category"),
    path("tag/<str:tag_slug>/", views.BlogListView.as_view(), name="tag"),
    path("<str:slug>/", views.BlogDetailView.as_view(), name="detail"),
]

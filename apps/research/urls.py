from django.urls import path

from . import views

app_name = "research"

urlpatterns = [
    path("", views.ResearchListView.as_view(), name="list"),
    path("<int:pk>/", views.legacy_redirect, name="legacy_detail"),
    path("<str:slug>/", views.ResearchDetailView.as_view(), name="detail"),
    path("<str:slug>/download/", views.download_pdf, name="download"),
]

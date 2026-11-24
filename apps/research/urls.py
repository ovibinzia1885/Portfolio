from django.urls import path

from . import views

app_name = "research"

urlpatterns = [
    path("", views.ResearchListView.as_view(), name="list"),
    path("<int:pk>/", views.ResearchDetailView.as_view(), name="detail"),
    path("<int:pk>/download/", views.download_pdf, name="download"),
]

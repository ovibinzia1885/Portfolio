from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("cv/download/", views.download_cv, name="download_cv"),
]

from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("cv/", views.cv_preview, name="cv_preview"),
    path("cv/view/", views.cv_inline, name="cv_inline"),
    path("cv/download/", views.download_cv, name="download_cv"),
]

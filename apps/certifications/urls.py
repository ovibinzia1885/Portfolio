from django.urls import path

from . import views

app_name = "certifications"

urlpatterns = [
    path("", views.CertificationListView.as_view(), name="list"),
]

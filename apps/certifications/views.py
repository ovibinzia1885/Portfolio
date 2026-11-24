from django.views.generic import ListView

from .models import Certification


class CertificationListView(ListView):
    model = Certification
    template_name = "certifications/list.html"
    context_object_name = "certifications"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        certs = context["certifications"]
        providers = []
        for cert in certs:
            if cert.issuing_organization not in providers:
                providers.append(cert.issuing_organization)
        latest = max((c.issue_date for c in certs if c.issue_date), default=None)
        context["providers"] = providers
        context["latest_issue"] = latest
        return context

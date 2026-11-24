from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from .models import Research


class ResearchListView(ListView):
    model = Research
    template_name = "research/list.html"
    context_object_name = "papers"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        self.type = self.request.GET.get("type", "")
        if self.type in Research.PublicationType.values:
            queryset = queryset.filter(publication_type=self.type)
        else:
            self.type = ""
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["types"] = Research.PublicationType.choices
        context["active_type"] = self.type
        return context


class ResearchDetailView(DetailView):
    model = Research
    template_name = "research/detail.html"
    context_object_name = "paper"


def download_pdf(request, pk):
    """Serve the research PDF as an attachment."""
    paper = get_object_or_404(Research, pk=pk)
    if not paper.pdf:
        raise Http404("No PDF available.")
    return FileResponse(
        paper.pdf.open("rb"), as_attachment=True, filename=paper.pdf.name.split("/")[-1]
    )

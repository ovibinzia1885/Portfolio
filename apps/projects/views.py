from django.views.generic import DetailView, ListView

from .models import Project, ProjectType


def collect_technologies(projects):
    """Unique technology names (case-insensitive) across projects, sorted."""
    seen = {}
    for project in projects:
        for tech in project.technology_list:
            seen.setdefault(tech.lower(), tech)
    return [(key, seen[key]) for key in sorted(seen)]


GROUP_META = {
    ProjectType.CLIENT: ("Client Projects", "bi-briefcase", "Work delivered for clients and organisations."),
    ProjectType.PERSONAL: ("Personal Projects", "bi-lightbulb", "Side projects, experiments and open-source work."),
}


def group_projects(projects):
    """Split projects into the two display groups (client, personal)."""
    projects = list(projects)
    groups = []
    for value, (label, icon, subtitle) in GROUP_META.items():
        items = [p for p in projects if p.project_type == value]
        groups.append({
            "key": value, "label": label, "icon": icon, "subtitle": subtitle,
            "projects": items, "technologies": collect_technologies(items),
        })
    return groups


class ProjectListView(ListView):
    template_name = "projects/list.html"
    context_object_name = "projects"

    def get_queryset(self):
        return Project.objects.prefetch_related("images")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project_groups"] = group_projects(context["projects"])
        return context


class ProjectDetailView(DetailView):
    model = Project
    template_name = "projects/detail.html"
    context_object_name = "project"

    def get_queryset(self):
        return Project.objects.prefetch_related("images")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["other_projects"] = (
            Project.objects.exclude(pk=self.object.pk).prefetch_related("images")[:3]
        )
        return context

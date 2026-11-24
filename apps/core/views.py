from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.views.generic import TemplateView

from apps.achievements.models import Achievement
from apps.blogs.models import BlogPost
from apps.certifications.models import Certification
from apps.contact.forms import ContactForm
from apps.education.models import Education
from apps.experience.models import Experience
from apps.projects.models import Project
from apps.projects.views import group_projects
from apps.research.models import Research
from apps.skills.models import MainCategory, Skill
from apps.training.models import Training

from .models import Profile

SKILL_ICONS = {
    MainCategory.TECHNICAL: "bi-cpu",
    MainCategory.PROJECT_MANAGEMENT: "bi-kanban",
    MainCategory.SOFT: "bi-people",
}


def group_skills():
    """Group skills as main category -> subcategory -> skills (empty groups skipped)."""
    skills = Skill.objects.select_related("subcategory")
    groups = []
    for value, label in MainCategory.choices:
        subgroups = {}
        for skill in (s for s in skills if s.main_category == value):
            key = skill.subcategory_id
            name = skill.subcategory.name if skill.subcategory else "General"
            subgroups.setdefault(key, {"name": name, "skills": []})["skills"].append(skill)
        if subgroups:
            groups.append({
                "key": value,
                "label": label,
                "icon": SKILL_ICONS[value],
                "subgroups": list(subgroups.values()),
            })
    return groups


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        featured = list(
            Project.objects.filter(is_featured=True).prefetch_related("images")[:6]
        )
        context.update(
            educations=Education.objects.all(),
            experiences=Experience.objects.all(),
            skill_groups=group_skills(),
            project_groups=group_projects(featured),
            has_featured_projects=bool(featured),
            achievements=Achievement.objects.all()[:6],
            certifications=Certification.objects.all()[:4],
            hero_skills=Skill.objects.filter(main_category=MainCategory.TECHNICAL)[:5],
            trainings=Training.objects.all(),
            latest_posts=(
                BlogPost.objects.published().select_related("category")[:3]
            ),
            papers=Research.objects.all()[:4],
            form=ContactForm(),
            stats={
                "projects": Project.objects.count(),
                "certifications": Certification.objects.count(),
                "papers": Research.objects.count(),
            },
        )
        return context


def _profile_with_cv():
    profile = Profile.objects.first()
    if not profile or not profile.resume:
        raise Http404("No CV uploaded.")
    return profile


def download_cv(request):
    """Serve the uploaded CV as an attachment."""
    profile = _profile_with_cv()
    return FileResponse(
        profile.resume.open("rb"),
        as_attachment=True,
        filename=profile.resume.name.split("/")[-1],
    )


def cv_preview(request):
    """Page that embeds the CV (PDF) with preview and download buttons."""
    profile = _profile_with_cv()
    if not profile.resume_is_pdf:  # non-PDF files cannot be previewed
        return redirect("core:download_cv")
    return render(request, "core/cv.html", {"cv_name": profile.resume.name.split("/")[-1]})


def cv_inline(request):
    """Serve the PDF inline so it can be shown inside the preview page."""
    profile = _profile_with_cv()
    if not profile.resume_is_pdf:
        raise Http404("CV is not a PDF.")
    return FileResponse(
        profile.resume.open("rb"),
        as_attachment=False,
        content_type="application/pdf",
        filename=profile.resume.name.split("/")[-1],
    )

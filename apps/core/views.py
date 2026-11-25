import re
from pathlib import PurePosixPath

from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
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
from .sections import visible_sections

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
                "icon": SKILL_ICONS.get(value, "bi-tools"),
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
        user = self.request.user
        context.update(
            home_sections=visible_sections(self.request, is_staff=user.is_authenticated and user.is_staff),
            educations=Education.objects.all(),
            experiences=Experience.objects.all(),
            skill_groups=group_skills(),
            # on the home page, a group with no featured project is left out
            project_groups=[g for g in group_projects(featured) if g["projects"]],
            has_featured_projects=bool(featured),
            achievements=Achievement.objects.all(),
            certifications=Certification.objects.all()[:4],
            hero_skills=Skill.objects.filter(main_category=MainCategory.TECHNICAL)[:5],
            trainings=Training.objects.all(),
            latest_posts=(
                BlogPost.objects.published().select_related("category").prefetch_related("tags")[:3]
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


def robots_txt(request):
    """robots.txt: allow everything public, point crawlers to the sitemap."""
    lines = [
        "User-agent: *",
        "Disallow: /cv/view/",
        "",
        f"Sitemap: {request.build_absolute_uri(reverse('sitemap'))}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


def _profile_with_cv():
    profile = Profile.objects.first()
    if not profile or not profile.resume_available:  # no CV, or the file is missing on disk
        raise Http404("No CV uploaded.")
    return profile


def cv_filename(profile):
    """Clean download name from the owner's name, e.g. "Nazmul_Hoque_Ovy_CV.pdf"
    (the stored name can carry a random suffix added by Django on re-upload)."""
    ext = PurePosixPath(profile.resume.name).suffix.lower() or ".pdf"
    name = re.sub(r"[^A-Za-z0-9]+", "_", profile.full_name).strip("_") or "CV"
    return f"{name}_CV{ext}"


def _serve_cv(profile, **kwargs):
    try:
        handle = profile.resume.open("rb")
    except OSError:  # removed between the check and the read
        raise Http404("CV file not found.")
    return FileResponse(handle, filename=cv_filename(profile), **kwargs)


def download_cv(request):
    """Serve the uploaded CV as an attachment."""
    return _serve_cv(_profile_with_cv(), as_attachment=True)


def cv_preview(request):
    """Page that embeds the CV (PDF) with preview and download buttons."""
    profile = _profile_with_cv()
    if not profile.resume_is_pdf:  # non-PDF files cannot be previewed
        return redirect("core:download_cv")
    return render(request, "core/cv.html", {"cv_name": cv_filename(profile)})


def serve_media_file(request, name):
    """Uploaded documents stored on Cloudinary (certificates, papers): served inline through this site."""
    import mimetypes

    from django.core.files.storage import default_storage

    if ".." in name.split("/") or name.startswith("/"):
        raise Http404
    try:
        handle = default_storage.open(name, "rb")
    except OSError:
        raise Http404("File not found.")
    content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
    response = FileResponse(handle, content_type=content_type, filename=PurePosixPath(name).name)
    response["Cache-Control"] = "public, max-age=86400"
    return response


def cv_inline(request):
    """Serve the PDF inline so it can be shown inside the preview page."""
    profile = _profile_with_cv()
    if not profile.resume_is_pdf:
        raise Http404("CV is not a PDF.")
    return _serve_cv(profile, as_attachment=False, content_type="application/pdf")

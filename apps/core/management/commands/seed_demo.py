"""Create (or remove) clearly-marked PLACEHOLDER content for design/testing.

Usage:
    python manage.py seed_demo           # create sample content
    python manage.py seed_demo --clear   # delete everything this command created

Every record created here starts with "[Sample]" so it is easy to spot and replace.
"""

import io
from datetime import date, timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw

from apps.achievements.models import Achievement
from apps.blogs.models import BlogCategory, BlogPost, BlogTag
from apps.certifications.models import Certification
from apps.core.models import Profile
from apps.education.models import Education
from apps.experience.models import Experience
from apps.projects.models import Project, ProjectImage
from apps.research.models import Research
from apps.skills.models import MainCategory, Skill, SkillSubcategory
from apps.training.models import Training

MARK = "[Sample] "

PALETTES = [
    ((99, 102, 241), (34, 211, 238)),
    ((236, 72, 153), (251, 146, 60)),
    ((16, 185, 129), (59, 130, 246)),
    ((245, 158, 11), (239, 68, 68)),
]

# Minimal valid one-page PDF used as a placeholder CV / paper.
SAMPLE_PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 144]/Contents 4 0 R"
    b"/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
    b"4 0 obj<</Length 56>>stream\nBT /F1 14 Tf 20 70 Td (SAMPLE PLACEHOLDER PDF) Tj ET\nendstream endobj\n"
    b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"trailer<</Root 1 0 R/Size 6>>\n%%EOF\n"
)


def make_image(label, index=0, size=(1200, 750)):
    """Gradient placeholder image with a label; returns PNG bytes."""
    c1, c2 = PALETTES[index % len(PALETTES)]
    width, height = size
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    for x in range(width):
        t = x / (width - 1)
        draw.line([(x, 0), (x, height)], fill=tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)))
    draw.text((width // 2, height // 2), label, fill="white", anchor="mm")
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def png(label, index=0, size=(1200, 750)):
    return ContentFile(make_image(label, index, size))


class Command(BaseCommand):
    help = "Create or remove clearly marked placeholder ([Sample]) content."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Delete all [Sample] records.")

    def handle(self, *args, **options):
        if options["clear"]:
            self.clear()
        elif Education.objects.filter(institution_name__startswith=MARK).exists():
            self.stdout.write("Sample content already exists. Use --clear first to recreate it.")
        else:
            with transaction.atomic():
                self.seed()
            self.stdout.write(self.style.SUCCESS("Sample content created. Remove it with: manage.py seed_demo --clear"))

    # ------------------------------------------------------------------ clear
    def clear(self):
        targets = [
            (Profile, "full_name"), (Education, "institution_name"), (Experience, "company"),
            (Skill, "name"), (Project, "title"), (Achievement, "title"),
            (Certification, "name"), (Training, "title"), (BlogPost, "title"),
            (BlogCategory, "name"), (BlogTag, "name"), (Research, "title"),
        ]
        total = 0
        for model, field in targets:
            deleted, _ = model.objects.filter(**{f"{field}__startswith": MARK}).delete()
            total += deleted
        self.stdout.write(self.style.SUCCESS(f"Removed {total} sample records."))

    # ------------------------------------------------------------------- seed
    def seed(self):
        today = date.today()

        if Profile.objects.exclude(full_name__startswith=MARK).exists():
            self.stdout.write("A real profile exists; skipping sample profile.")
        else:
            self.seed_profile()
        self.seed_content(today)

    def seed_profile(self):
        profile = Profile.objects.create(
            full_name=f"{MARK}Your Name",
            headline="QA Automation Engineer & Software Tester",
            short_intro="PLACEHOLDER: Replace this with a short, punchy introduction about what you do and the value you deliver.",
            bio=(
                "PLACEHOLDER BIO. Replace with your own story.\n\n"
                "Write two or three short paragraphs here: who you are, what you specialise in, "
                "the kind of problems you enjoy solving and what you are looking for next."
            ),
            email="sample@example.com", phone="+000 000 000 000", location="City, Country",
            github_url="https://github.com/your-username",
            linkedin_url="https://www.linkedin.com/in/your-username",
            facebook_url="https://www.facebook.com/your-username",
        )
        profile.photo.save("sample-profile.png", png("PHOTO", 0, (800, 800)), save=False)
        profile.resume.save("sample-cv.pdf", ContentFile(SAMPLE_PDF), save=True)

    def seed_content(self, today):
        Education.objects.create(
            institution_name=f"{MARK}Example University", degree="B.Sc.", field_of_study="Computer Science & Engineering",
            department="Department of CSE", start_date=date(2018, 1, 1), end_date=date(2021, 12, 31),
            passing_year=2021, cgpa="3.75", scale="4.00", institution_website="https://example.com",
            description="PLACEHOLDER: Add notable coursework, thesis or activities.", display_order=1,
        )
        Education.objects.create(
            institution_name=f"{MARK}Example College", degree="HSC", field_of_study="Science",
            department="Science Group", start_date=date(2016, 1, 1), end_date=date(2017, 12, 31),
            passing_year=2017, cgpa="5.00", scale="5.00", display_order=2,
        )

        exp1 = Experience.objects.create(
            company=f"{MARK}Example Tech Ltd.", company_url="https://example.com", designation="Senior QA Engineer",
            employment_type="full_time", start_date=date(2023, 1, 1), is_current=True,
            responsibilities="PLACEHOLDER: Design and maintain automated test suites\nPlan and estimate testing for each release\nMentor junior engineers",
            achievements="PLACEHOLDER: Reduced regression time by 60%\nIntroduced CI test pipeline",
            technologies="Selenium, Python, Postman, Jenkins", display_order=1,
        )
        exp1.company_logo.save("sample-logo-1.png", png("LOGO", 1, (300, 300)), save=True)
        exp2 = Experience.objects.create(
            company=f"{MARK}Sample Software Inc.", designation="QA Engineer", employment_type="full_time",
            start_date=date(2021, 1, 1), end_date=date(2022, 12, 31),
            responsibilities="PLACEHOLDER: Manual and API testing\nWrote test cases and bug reports",
            technologies="Manual Testing, JIRA, SQL", display_order=2,
        )
        exp2.company_logo.save("sample-logo-2.png", png("LOGO", 2, (300, 300)), save=True)

        self.seed_skills()

        projects = [
            ("Test Automation Framework", "Python, Selenium, Pytest", True, "client"),
            ("API Testing Suite", "Postman, Python, CI/CD", True, "client"),
            ("Portfolio Website", "Django, Bootstrap, JavaScript", True, "personal"),
            ("Performance Dashboard", "JMeter, Grafana, Docker", False, "personal"),
        ]
        for i, (title, tech, featured, kind) in enumerate(projects):
            project = Project.objects.create(
                title=f"{MARK}{title}", project_type=kind,
                client_name="Example Client Ltd." if kind == "client" else "", summary="PLACEHOLDER: One-sentence summary of what this project does.",
                description="PLACEHOLDER DESCRIPTION.\n\nExplain the problem, your approach, your role and the result.",
                technologies=tech, live_url="https://example.com", repository_url="https://github.com/your-username/repo",
                start_date=today - timedelta(days=400 - i * 60), is_featured=featured, display_order=i,
            )
            for n in range(1 + i % 3):
                ProjectImage.objects.create(
                    project=project, caption=f"Screenshot {n + 1}", display_order=n,
                    image=ContentFile(make_image(f"PROJECT {i + 1} / IMG {n + 1}", i + n), name=f"sample-project-{i}-{n}.png"),
                )

        for i in range(3):
            ach = Achievement.objects.create(
                title=f"{MARK}Award {i + 1}", organization="Example Organization", date=today - timedelta(days=200 * (i + 1)),
                description="PLACEHOLDER: Describe the achievement and why it mattered.", display_order=i,
            )
            if i == 0:
                ach.image.save("sample-achievement.png", png("AWARD", 3), save=True)

        for i, name in enumerate(["ISTQB Certified Tester", "Python for Automation", "Agile & Scrum Fundamentals"]):
            Certification.objects.create(
                name=f"{MARK}{name}", issuing_organization="Example Authority", issue_date=today - timedelta(days=300 * (i + 1)),
                credential_id=f"SAMPLE-{1000 + i}", credential_url="https://example.com/verify", display_order=i,
            )

        for i, name in enumerate(["Advanced Test Automation Workshop", "Software Testing Bootcamp"]):
            Training.objects.create(
                title=f"{MARK}{name}", provider="Example Academy", location="Online",
                start_date=today - timedelta(days=500 + i * 200), end_date=today - timedelta(days=450 + i * 200),
                duration="6 weeks", description="PLACEHOLDER: What you learned.", display_order=i,
            )

        self.seed_blog()

        for i, (kind, title) in enumerate([
            ("journal", "Placeholder Research Paper on Test Automation"),
            ("conference", "Placeholder Conference Paper on API Quality"),
            ("thesis", "Placeholder Undergraduate Thesis"),
        ]):
            paper = Research.objects.create(
                title=f"{MARK}{title}", authors="Your Name, Co-Author", publication_type=kind,
                venue="Example Journal of Computing", publication_date=today - timedelta(days=250 * (i + 1)),
                abstract="PLACEHOLDER ABSTRACT. Summarise the problem, method, results and conclusion of the paper in a short paragraph.",
                doi="10.0000/sample", url="https://example.com/paper", display_order=i,
            )
            paper.pdf.save(f"sample-paper-{i}.pdf", ContentFile(SAMPLE_PDF), save=True)

    def seed_skills(self):
        plan = {
            MainCategory.TECHNICAL: {
                "Automation Testing": [("Selenium", "advanced"), ("Cypress", "intermediate")],
                "Programming Languages": [("Python", "advanced"), ("JavaScript", "intermediate")],
                "API Testing": [("Postman", "expert"), ("REST Assured", "intermediate")],
                "CI/CD and DevOps": [("Jenkins", "intermediate"), ("Docker", "beginner")],
            },
            MainCategory.PROJECT_MANAGEMENT: {
                "Test Planning and Estimation": [("Test Planning", "advanced")],
                "Risk and Issue Management": [("Risk Assessment", "intermediate")],
            },
            MainCategory.SOFT: {None: [("Communication", "advanced"), ("Problem Solving", "expert")]},
        }
        for main, groups in plan.items():
            for sub_name, skills in groups.items():
                sub = None
                if sub_name:
                    sub, _ = SkillSubcategory.objects.get_or_create(main_category=main, name=sub_name)
                for order, (name, level) in enumerate(skills):
                    Skill.objects.create(
                        name=f"{MARK}{name}", main_category=main, subcategory=sub,
                        experience_level=level, display_order=order,
                    )

    def seed_blog(self):
        categories = [BlogCategory.objects.create(name=f"{MARK}{n}") for n in ("Testing", "Django")]
        tags = [BlogTag.objects.create(name=f"{MARK}{n}") for n in ("python", "automation", "career", "tips")]
        body = (
            "PLACEHOLDER ARTICLE BODY.\n\n"
            + "Replace this text with your own article. " * 25
            + "\n\nUse blank lines to separate paragraphs."
        )
        now = timezone.now()
        for i in range(8):
            post = BlogPost.objects.create(
                title=f"{MARK}Sample Article {i + 1}",
                excerpt="PLACEHOLDER: A short teaser that appears on blog cards.",
                content=body, category=categories[i % 2],
                status="draft" if i == 7 else "published",
                published_at=None if i == 7 else now - timedelta(days=i * 5),
            )
            post.tags.set(tags[i % 4: i % 4 + 2])
            if i < 5:
                post.cover_image.save(f"sample-blog-{i}.png", png(f"BLOG {i + 1}", i), save=True)

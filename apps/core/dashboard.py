"""Data for the admin dashboard (templates/admin/index.html), exposed as the `dashboard` tag in portfolio_extras."""

from django.urls import NoReverseMatch, reverse

# (app_label, model_name, label, icon)
CARDS = [
    ("experience", "experience", "Experience", "bi-briefcase"),
    ("projects", "project", "Projects", "bi-kanban"),
    ("skills", "skill", "Skills", "bi-cpu"),
    ("certifications", "certification", "Certifications", "bi-patch-check"),
    ("achievements", "achievement", "Awards", "bi-trophy"),
    ("research", "research", "Publications", "bi-journal-text"),
    ("blogs", "blogpost", "Blog posts", "bi-pencil-square"),
    ("contact", "contactmessage", "Messages", "bi-envelope"),
]
QUICK_ADD = [
    ("projects", "project", "Project"),
    ("certifications", "certification", "Certification"),
    ("achievements", "achievement", "Award"),
    ("research", "research", "Publication"),
    ("blogs", "blogpost", "Blog post"),
]


def _url(name, *args):
    try:
        return reverse(name, args=args)
    except NoReverseMatch:
        return ""


def dashboard(context):
    from django.apps import apps

    user = context["request"].user
    cards = []
    for app_label, model_name, label, icon in CARDS:
        model = apps.get_model(app_label, model_name)
        if not user.has_perm(f"{app_label}.view_{model_name}"):
            continue
        extra = ""
        if model_name == "contactmessage":
            unread = model.objects.filter(is_read=False).count()
            extra = f"{unread} unread" if unread else "all read"
        cards.append({
            "label": label, "icon": icon, "count": model.objects.count(), "extra": extra,
            "url": _url(f"admin:{app_label}_{model_name}_changelist"),
        })
    quick = [
        {"label": label, "url": _url(f"admin:{app_label}_{model_name}_add")}
        for app_label, model_name, label in QUICK_ADD
        if user.has_perm(f"{app_label}.add_{model_name}")
    ]
    profile_model = apps.get_model("core", "profile")
    profile = profile_model.objects.first()
    profile_url = (_url("admin:core_profile_change", profile.pk) if profile
                   else _url("admin:core_profile_add"))
    visits = None
    if user.has_perm("analytics.view_dailyvisitor"):
        from apps.analytics.stats import dashboard_stats

        visits = dashboard_stats()
        visits["visitors_url"] = _url("admin:analytics_dailyvisitor_changelist")
        visits["pages_url"] = _url("admin:analytics_pageviewstat_changelist")
    from django.conf import settings

    return {"cards": cards, "quick": quick, "profile": profile, "profile_url": profile_url, "visits": visits,
            "warning": getattr(settings, "CLOUDINARY_URL_PROBLEM", "")}

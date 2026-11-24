from django.db import migrations

TECHNICAL = [
    "Automation Testing",
    "Programming Languages",
    "API Testing",
    "Manual Testing",
    "Performance Testing",
    "Test Automation Frameworks",
    "CI/CD and DevOps",
    "Database Testing",
    "Security Testing",
    "Version Control",
    "Test Management Tools",
    "Agile Methodologies",
]

PROJECT_MANAGEMENT = [
    "Project Planning and Coordination",
    "Test Planning and Estimation",
    "Test Strategy Development",
    "Task Prioritization",
    "Resource Allocation",
    "Risk and Issue Management",
    "Project Monitoring and Reporting",
    "Stakeholder Management",
    "Cross-functional Team Coordination",
    "Agile and Scrum Project Management",
    "Requirement Analysis",
    "Defect Tracking and Management",
]

# Soft skills list was incomplete in the request; add them via Django admin.


def seed(apps, schema_editor):
    Subcategory = apps.get_model("skills", "SkillSubcategory")
    for main, names in (("technical", TECHNICAL), ("project_management", PROJECT_MANAGEMENT)):
        for order, name in enumerate(names, start=1):
            Subcategory.objects.get_or_create(
                main_category=main, name=name, defaults={"display_order": order}
            )


def unseed(apps, schema_editor):
    apps.get_model("skills", "SkillSubcategory").objects.filter(
        name__in=TECHNICAL + PROJECT_MANAGEMENT
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("skills", "0002_alter_skill_options_remove_skill_category_and_more")]
    operations = [migrations.RunPython(seed, unseed)]

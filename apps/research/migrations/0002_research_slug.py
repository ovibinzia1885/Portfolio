from django.db import migrations, models


def fill_slugs(apps, schema_editor):
    """Give existing papers a unique slug built from their title."""
    from django.utils.text import slugify

    Research = apps.get_model("research", "Research")
    used = set()
    for paper in Research.objects.order_by("pk"):
        base = (slugify(paper.title, allow_unicode=True) or "paper")[:300]
        slug, n = base, 2
        while slug in used:
            slug, n = f"{base}-{n}", n + 1
        used.add(slug)
        paper.slug = slug
        paper.save(update_fields=["slug"])


class Migration(migrations.Migration):
    dependencies = [("research", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="research",
            name="slug",
            field=models.SlugField(
                allow_unicode=True, blank=True, max_length=320, default="", db_index=False
            ),
            preserve_default=False,
        ),
        migrations.RunPython(fill_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="research",
            name="slug",
            field=models.SlugField(allow_unicode=True, blank=True, max_length=320, unique=True),
        ),
    ]

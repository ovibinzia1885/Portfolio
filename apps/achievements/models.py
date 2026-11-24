from django.db import models

from apps.core.models import OrderedModel


class Achievement(OrderedModel):
    title = models.CharField(max_length=200)
    organization = models.CharField(max_length=200, blank=True)
    date = models.DateField()
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="achievements/", blank=True)
    url = models.URLField(blank=True)

    class Meta(OrderedModel.Meta):
        ordering = ["display_order", "-date"]

    def __str__(self):
        return self.title

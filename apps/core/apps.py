from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'apps.core'
    verbose_name = "Profile & CV"

    def ready(self):
        from .images import connect

        connect()  # resize/compress large image uploads on save

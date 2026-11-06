from django.apps import AppConfig


class MangapageappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "MangaPageApp"

    def ready(self):
        import MangaPageApp.signals

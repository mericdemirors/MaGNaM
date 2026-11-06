from django.apps import AppConfig


class ProfilepageappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ProfilePageApp"

    def ready(self):
        import ProfilePageApp.signals

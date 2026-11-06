from django.apps import AppConfig


class PortfoliopageappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "PortfolioPageApp"

    def ready(self):
        import PortfolioPageApp.signals

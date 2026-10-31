from django.apps import AppConfig


class IssuesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "issues"

    def ready(self):
        # Import tasks modules so Celery autodiscover finds them from sibling apps.
        pass

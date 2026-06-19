from django.apps import AppConfig


class FeedbackConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "feedback"

    def ready(self):
        from horilla.horilla_settings import APPS
        APPS.append("feedback")
        super().ready()

from django.apps import AppConfig


class LmsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "lms"

    def ready(self):
        from horilla.horilla_settings import APPS

        APPS.append("lms")
        super().ready()

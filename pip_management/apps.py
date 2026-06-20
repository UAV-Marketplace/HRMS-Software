from django.apps import AppConfig


class PipManagementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pip_management"
    verbose_name = "Performance Improvement Plans"

    def ready(self):
        from horilla.horilla_settings import APPS
        APPS.append("pip_management")
        super().ready()

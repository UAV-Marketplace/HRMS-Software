from django.apps import AppConfig


class HrMeetingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "hr_meeting"

    def ready(self):
        from horilla.horilla_settings import APPS

        APPS.append("hr_meeting")
        super().ready()

from django.db import models
from django.utils.translation import gettext_lazy as _

from employee.models import Employee
from horilla.models import HorillaModel, upload_path


class HRMeetingRecord(HorillaModel):
    meeting_date = models.DateField(verbose_name=_("Date"))
    purpose = models.CharField(
        max_length=255, verbose_name=_("Purpose of Meeting")
    )
    people_involved = models.ManyToManyField(
        Employee,
        verbose_name=_("People Involved"),
        related_name="hr_meeting_records",
    )
    discussion = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Discussion"),
    )
    solutions = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Solutions"),
    )
    attachment = models.FileField(
        upload_to=upload_path,
        blank=True,
        null=True,
        verbose_name=_("Attachment"),
    )

    class Meta:
        verbose_name = _("HR Meeting Record")
        verbose_name_plural = _("HR Meeting Records")
        ordering = ["-meeting_date"]

    def __str__(self):
        return f"{self.purpose} ({self.meeting_date})"

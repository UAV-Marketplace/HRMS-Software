from django.db import models
from django.utils.translation import gettext_lazy as _

from employee.models import Employee
from horilla.models import HorillaModel


class EmployeeFeedback(HorillaModel):
    RATING_CHOICES = [
        (1, _("1 — Poor")),
        (2, _("2 — Below Average")),
        (3, _("3 — Average")),
        (4, _("4 — Good")),
        (5, _("5 — Excellent")),
    ]

    given_by = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="feedbacks_given",
        verbose_name=_("Given By"),
    )
    about_employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="feedbacks_received",
        verbose_name=_("About Employee"),
    )
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        verbose_name=_("Rating"),
    )
    feedback_text = models.TextField(verbose_name=_("Feedback"))

    class Meta:
        verbose_name = _("Employee Feedback")
        verbose_name_plural = _("Employee Feedbacks")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Feedback about {self.about_employee} (★{self.rating})"

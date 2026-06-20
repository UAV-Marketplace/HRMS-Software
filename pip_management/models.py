from django.db import models
from django.utils.translation import gettext_lazy as _

from employee.models import Employee
from horilla.models import HorillaModel


class PerformanceImprovementPlan(HorillaModel):
    STATUS_DRAFT = "draft"
    STATUS_ACTIVE = "active"
    STATUS_COMPLETED = "completed"
    STATUS_EXTENDED = "extended"
    STATUS_TERMINATED = "terminated"

    STATUS_CHOICES = [
        (STATUS_DRAFT, _("Draft")),
        (STATUS_ACTIVE, _("Active")),
        (STATUS_COMPLETED, _("Completed")),
        (STATUS_EXTENDED, _("Extended")),
        (STATUS_TERMINATED, _("Terminated")),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="pip_plans",
        verbose_name=_("Employee"),
    )
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(verbose_name=_("End Date"))
    reason = models.TextField(verbose_name=_("Reason / Performance Issues Observed"))
    objectives = models.TextField(verbose_name=_("Objectives / Expected Improvements"))
    support_provided = models.TextField(
        verbose_name=_("Support to be Provided"),
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        verbose_name=_("Status"),
    )
    outcome_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Outcome / Closing Notes"),
    )

    class Meta:
        verbose_name = _("Performance Improvement Plan")
        verbose_name_plural = _("Performance Improvement Plans")
        ordering = ["-created_at"]

    def __str__(self):
        return f"PIP — {self.employee} ({self.get_status_display()})"

    def goals_count(self):
        return self.goals.count()

    def achieved_goals_count(self):
        return self.goals.filter(is_achieved=True).count()

    def duration_days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return 0

    def status_color(self):
        return {
            "draft": "#6b7280",
            "active": "#6366f1",
            "completed": "#22c55e",
            "extended": "#f59e0b",
            "terminated": "#ef4444",
        }.get(self.status, "#6b7280")


class PIPGoal(models.Model):
    pip = models.ForeignKey(
        PerformanceImprovementPlan,
        on_delete=models.CASCADE,
        related_name="goals",
        verbose_name=_("PIP"),
    )
    description = models.TextField(verbose_name=_("Goal Description"))
    target_date = models.DateField(blank=True, null=True, verbose_name=_("Target Date"))
    is_achieved = models.BooleanField(default=False, verbose_name=_("Achieved"))
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("PIP Goal")
        verbose_name_plural = _("PIP Goals")
        ordering = ["created_at"]

    def __str__(self):
        return self.description[:80]


class PIPProgressReview(HorillaModel):
    pip = models.ForeignKey(
        PerformanceImprovementPlan,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("PIP"),
    )
    review_date = models.DateField(verbose_name=_("Review Date"))
    progress_notes = models.TextField(verbose_name=_("Progress Notes"))
    reviewed_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pip_reviews_conducted",
        verbose_name=_("Reviewed By"),
    )

    class Meta:
        verbose_name = _("PIP Progress Review")
        verbose_name_plural = _("PIP Progress Reviews")
        ordering = ["-review_date"]

    def __str__(self):
        return f"Review on {self.review_date} — {self.pip}"

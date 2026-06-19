from django.db import models
from django.utils.translation import gettext_lazy as _

from employee.models import Employee
from horilla.models import HorillaModel, upload_path


class Course(HorillaModel):
    title = models.CharField(max_length=200, verbose_name=_("Course Title"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    drive_link = models.URLField(max_length=500, verbose_name=_("Drive Link"))
    thumbnail = models.ImageField(
        upload_to=upload_path, blank=True, null=True, verbose_name=_("Thumbnail")
    )

    class Meta:
        verbose_name = _("Course")
        verbose_name_plural = _("Courses")
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def question_count(self):
        return self.questions.filter(is_active=True).count()

    def assignment_count(self):
        return self.assignments.count()


class CourseAssignment(HorillaModel):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name=_("Course"),
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="course_assignments",
        verbose_name=_("Employee"),
    )
    is_completed = models.BooleanField(default=False, verbose_name=_("Completed"))
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("course", "employee")
        verbose_name = _("Course Assignment")
        verbose_name_plural = _("Course Assignments")

    def __str__(self):
        return f"{self.employee} — {self.course}"

    def latest_attempt(self):
        return self.test_attempts.order_by("-started_at").first()

    def passed_attempt(self):
        return self.test_attempts.filter(passed=True).first()

    def attempts_taken(self):
        return self.test_attempts.filter(is_submitted=True).count()


class LMSQuestion(HorillaModel):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name=_("Course"),
    )
    question_text = models.TextField(verbose_name=_("Question"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Order"))

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")
        ordering = ["order", "id"]

    def __str__(self):
        return self.question_text[:80]


class LMSQuestionOption(HorillaModel):
    question = models.ForeignKey(
        LMSQuestion,
        on_delete=models.CASCADE,
        related_name="options",
        verbose_name=_("Question"),
    )
    option_text = models.CharField(max_length=500, verbose_name=_("Option Text"))
    is_correct = models.BooleanField(default=False, verbose_name=_("Correct"))

    class Meta:
        verbose_name = _("Option")
        verbose_name_plural = _("Options")

    def __str__(self):
        return self.option_text


class TestConfiguration(HorillaModel):
    course = models.OneToOneField(
        Course,
        on_delete=models.CASCADE,
        related_name="test_config",
        verbose_name=_("Course"),
    )
    duration_minutes = models.PositiveIntegerField(
        default=30, verbose_name=_("Duration (minutes)")
    )
    pass_percentage = models.PositiveIntegerField(
        default=70, verbose_name=_("Pass Percentage (%)")
    )
    max_attempts = models.PositiveIntegerField(
        default=3, verbose_name=_("Max Attempts")
    )
    instructions = models.TextField(
        blank=True, null=True, verbose_name=_("Test Instructions")
    )

    class Meta:
        verbose_name = _("Test Configuration")
        verbose_name_plural = _("Test Configurations")

    def __str__(self):
        return f"Config — {self.course}"


class TestAttempt(HorillaModel):
    assignment = models.ForeignKey(
        CourseAssignment,
        on_delete=models.CASCADE,
        related_name="test_attempts",
        verbose_name=_("Assignment"),
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(default=0, verbose_name=_("Score (%)"))
    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    passed = models.BooleanField(default=False)
    attempt_number = models.PositiveIntegerField(default=1)
    tab_switch_count = models.PositiveIntegerField(
        default=0, verbose_name=_("Tab Switches")
    )
    is_suspicious = models.BooleanField(
        default=False, verbose_name=_("Suspicious Activity")
    )
    is_submitted = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Test Attempt")
        verbose_name_plural = _("Test Attempts")
        ordering = ["-started_at"]

    def __str__(self):
        return (
            f"{self.assignment.employee} — {self.assignment.course} "
            f"(Attempt {self.attempt_number})"
        )


class TestAnswer(models.Model):
    attempt = models.ForeignKey(
        TestAttempt, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(LMSQuestion, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(
        LMSQuestionOption, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        unique_together = ("attempt", "question")

    def is_correct(self):
        return bool(self.selected_option and self.selected_option.is_correct)

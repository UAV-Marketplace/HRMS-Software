from django import forms
from django.utils.translation import gettext_lazy as _

from base.forms import ModelForm
from pip_management.models import PIPGoal, PIPProgressReview, PerformanceImprovementPlan


class PIPForm(ModelForm):
    class Meta:
        model = PerformanceImprovementPlan
        fields = [
            "employee",
            "start_date",
            "end_date",
            "reason",
            "objectives",
            "support_provided",
            "status",
            "outcome_notes",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reason"].widget.attrs.update({
            "rows": 4,
            "placeholder": _("Describe the performance issues or concerns observed…"),
        })
        self.fields["objectives"].widget.attrs.update({
            "rows": 4,
            "placeholder": _("List the specific improvements or targets the employee must achieve…"),
        })
        self.fields["support_provided"].widget.attrs.update({
            "rows": 3,
            "placeholder": _("Describe the training, mentoring, or resources that will be provided…"),
        })
        self.fields["outcome_notes"].widget.attrs.update({
            "rows": 3,
            "placeholder": _("Fill this when closing or completing the PIP…"),
        })
        self.fields["outcome_notes"].required = False
        self.fields["support_provided"].required = False


class PIPGoalForm(forms.ModelForm):
    class Meta:
        model = PIPGoal
        fields = ["description", "target_date", "notes"]
        widgets = {
            "description": forms.Textarea(attrs={
                "class": "oh-input w-100",
                "rows": 3,
                "placeholder": _("Describe the specific goal or milestone…"),
            }),
            "target_date": forms.DateInput(attrs={
                "class": "oh-input w-100",
                "type": "date",
            }),
            "notes": forms.Textarea(attrs={
                "class": "oh-input w-100",
                "rows": 2,
                "placeholder": _("Additional context or success criteria…"),
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["target_date"].required = False
        self.fields["notes"].required = False


class PIPReviewForm(forms.ModelForm):
    class Meta:
        model = PIPProgressReview
        fields = ["review_date", "progress_notes"]
        widgets = {
            "review_date": forms.DateInput(attrs={
                "class": "oh-input w-100",
                "type": "date",
            }),
            "progress_notes": forms.Textarea(attrs={
                "class": "oh-input w-100",
                "rows": 4,
                "placeholder": _("Summarise the employee's progress since the last review…"),
            }),
        }

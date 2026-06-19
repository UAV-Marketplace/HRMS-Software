from django import forms
from django.utils.translation import gettext_lazy as _

from base.forms import ModelForm
from employee.models import Employee
from feedback.models import EmployeeFeedback


class FeedbackForm(ModelForm):
    class Meta:
        model = EmployeeFeedback
        fields = ["about_employee", "rating", "feedback_text"]

    def __init__(self, *args, exclude_employee=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Employee.objects.filter(is_active=True)
        if exclude_employee:
            qs = qs.exclude(id=exclude_employee.id)
        self.fields["about_employee"].queryset = qs
        self.fields["about_employee"].label = _("Select Employee")
        self.fields["rating"].widget = forms.HiddenInput()
        self.fields["feedback_text"].widget.attrs.update({
            "rows": 5,
            "placeholder": _("Share honest feedback about this employee's performance, teamwork, and attitude..."),
        })

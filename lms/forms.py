from django import forms
from django.utils.translation import gettext_lazy as _

from base.forms import ModelForm
from employee.models import Employee
from lms.models import Course, TestConfiguration

_INPUT = "oh-input w-100 form-control"
_SELECT = "oh-select oh-select-2"


class CourseForm(ModelForm):
    class Meta:
        model = Course
        fields = ["title", "description", "drive_link", "thumbnail"]
        exclude = ["is_active"]


class QuestionForm(forms.Form):
    question_text = forms.CharField(
        label=_("Question"),
        widget=forms.Textarea(attrs={"class": _INPUT, "rows": 3}),
    )
    option_a = forms.CharField(
        label=_("Option A"),
        widget=forms.TextInput(attrs={"class": _INPUT}),
    )
    option_b = forms.CharField(
        label=_("Option B"),
        widget=forms.TextInput(attrs={"class": _INPUT}),
    )
    option_c = forms.CharField(
        label=_("Option C"),
        widget=forms.TextInput(attrs={"class": _INPUT}),
    )
    option_d = forms.CharField(
        label=_("Option D"),
        widget=forms.TextInput(attrs={"class": _INPUT}),
    )
    correct_option = forms.ChoiceField(
        label=_("Correct Answer"),
        choices=[("a", "A"), ("b", "B"), ("c", "C"), ("d", "D")],
        widget=forms.RadioSelect(),
    )


class TestConfigForm(ModelForm):
    class Meta:
        model = TestConfiguration
        fields = ["duration_minutes", "pass_percentage", "max_attempts", "instructions"]
        exclude = ["is_active"]


class CourseAssignForm(forms.Form):
    employees = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        widget=forms.SelectMultiple(attrs={"class": _SELECT}),
        label=_("Select Employees"),
    )

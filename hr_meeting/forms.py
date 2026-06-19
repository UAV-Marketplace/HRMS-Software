from django import forms
from django.utils.translation import gettext_lazy as _

from base.forms import ModelForm
from hr_meeting.models import HRMeetingRecord


class HRMeetingRecordForm(ModelForm):
    class Meta:
        model = HRMeetingRecord
        fields = [
            "meeting_date",
            "purpose",
            "people_involved",
            "discussion",
            "solutions",
            "attachment",
        ]
        exclude = ["is_active"]
        widgets = {
            "meeting_date": forms.DateInput(attrs={"type": "date"}),
            "discussion": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": _(
                        "Mention what things are discussed in the meeting."
                    ),
                }
            ),
            "solutions": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": _("Mention the solutions offered by HR."),
                }
            ),
        }

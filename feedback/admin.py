from django.contrib import admin

from feedback.models import EmployeeFeedback


@admin.register(EmployeeFeedback)
class EmployeeFeedbackAdmin(admin.ModelAdmin):
    list_display = ["about_employee", "given_by", "rating", "created_at"]
    list_filter = ["rating"]
    search_fields = [
        "about_employee__employee_first_name",
        "given_by__employee_first_name",
    ]

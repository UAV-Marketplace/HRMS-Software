from django.contrib import admin

from pip_management.models import PIPGoal, PIPProgressReview, PerformanceImprovementPlan


@admin.register(PerformanceImprovementPlan)
class PIPAdmin(admin.ModelAdmin):
    list_display = ["employee", "start_date", "end_date", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["employee__employee_first_name", "employee__employee_last_name"]


admin.site.register(PIPGoal)
admin.site.register(PIPProgressReview)

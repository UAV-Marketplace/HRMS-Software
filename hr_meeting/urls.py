from django.urls import path

from hr_meeting import views

urlpatterns = [
    path("view/", views.hr_meeting_view, name="hr-meeting-view"),
    path("filter/", views.hr_meeting_filter, name="hr-meeting-filter"),
    path("create/", views.hr_meeting_create, name="hr-meeting-create"),
    path("update/<int:id>/", views.hr_meeting_update, name="hr-meeting-update"),
    path("delete/<int:id>/", views.hr_meeting_delete, name="hr-meeting-delete"),
]

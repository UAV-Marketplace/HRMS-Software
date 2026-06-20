from django.urls import path

from pip_management import views

urlpatterns = [
    # HR / Admin
    path("", views.pip_list, name="pip-list"),
    path("filter/", views.pip_filter, name="pip-filter"),
    path("create/", views.pip_create, name="pip-create"),
    path("<int:pip_id>/update/", views.pip_update, name="pip-update"),
    path("<int:pip_id>/delete/", views.pip_delete, name="pip-delete"),
    path("<int:pip_id>/detail/", views.pip_detail, name="pip-detail"),
    # Goals
    path("<int:pip_id>/goals/add/", views.pip_goal_add, name="pip-goal-add"),
    path("goals/<int:goal_id>/toggle/", views.pip_goal_toggle, name="pip-goal-toggle"),
    path("goals/<int:goal_id>/delete/", views.pip_goal_delete, name="pip-goal-delete"),
    # Reviews
    path("<int:pip_id>/reviews/add/", views.pip_review_add, name="pip-review-add"),
    # Employee
    path("my/", views.my_pip, name="pip-my"),
]

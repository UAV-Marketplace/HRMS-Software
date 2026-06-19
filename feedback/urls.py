from django.urls import path

from feedback import views

urlpatterns = [
    path("give/", views.give_feedback, name="feedback-give"),
    path("my/", views.my_feedback, name="feedback-my"),
    path("all/", views.all_feedback, name="feedback-all"),
]

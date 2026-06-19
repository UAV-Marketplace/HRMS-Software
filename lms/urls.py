from django.urls import path

from lms import views

urlpatterns = [
    # HR – courses
    path("courses/", views.lms_courses, name="lms-courses"),
    path("courses/filter/", views.lms_course_filter, name="lms-course-filter"),
    path("courses/create/", views.lms_course_create, name="lms-course-create"),
    path("courses/update/<int:id>/", views.lms_course_update, name="lms-course-update"),
    path("courses/delete/<int:id>/", views.lms_course_delete, name="lms-course-delete"),
    path("courses/<int:id>/assign/", views.lms_course_assign, name="lms-course-assign"),
    path("courses/<int:course_id>/assignments/", views.lms_manage_assignments, name="lms-manage-assignments"),
    path("assignments/<int:assignment_id>/unassign/", views.lms_course_unassign, name="lms-course-unassign"),
    # HR – questions
    path("courses/<int:course_id>/questions/", views.lms_question_management, name="lms-question-management"),
    path("courses/<int:course_id>/questions/create/", views.lms_question_create, name="lms-question-create"),
    path("questions/<int:question_id>/update/", views.lms_question_update, name="lms-question-update"),
    path("questions/<int:question_id>/delete/", views.lms_question_delete, name="lms-question-delete"),
    # HR – test config & results
    path("courses/<int:course_id>/test-config/", views.lms_test_config, name="lms-test-config"),
    path("results/", views.lms_results, name="lms-results"),
    # Employee
    path("my-courses/", views.my_courses, name="lms-my-courses"),
    path("my-courses/<int:assignment_id>/start/", views.start_test, name="lms-start-test"),
    path("test/<int:attempt_id>/", views.test_interface, name="lms-test-interface"),
    path("test/<int:attempt_id>/submit/", views.submit_test, name="lms-submit-test"),
    path("test/<int:attempt_id>/result/", views.test_result, name="lms-test-result"),
    path("test/<int:attempt_id>/tab-switch/", views.record_tab_switch, name="lms-record-tab-switch"),
]

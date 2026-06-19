from django.contrib import admin

from lms.models import (
    Course,
    CourseAssignment,
    LMSQuestion,
    LMSQuestionOption,
    TestAnswer,
    TestAttempt,
    TestConfiguration,
)

admin.site.register(Course)
admin.site.register(CourseAssignment)
admin.site.register(LMSQuestion)
admin.site.register(LMSQuestionOption)
admin.site.register(TestConfiguration)
admin.site.register(TestAttempt)
admin.site.register(TestAnswer)

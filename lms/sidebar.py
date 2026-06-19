from django.utils.translation import gettext_lazy as trans

MENU = trans("LMS")
IMG_SRC = "images/ui/pms.svg"

SUBMENUS = [
    {
        "menu": trans("Courses"),
        "redirect": "/lms/courses/",
        "accessibility": "lms.sidebar.courses_accessibility",
    },
    {
        "menu": trans("My Courses"),
        "redirect": "/lms/my-courses/",
    },
    {
        "menu": trans("Results"),
        "redirect": "/lms/results/",
        "accessibility": "lms.sidebar.results_accessibility",
    },
]


def courses_accessibility(request, submenu, user_perms, *args, **kwargs):
    return request.user.is_superuser or request.user.has_perm("lms.view_course")


def results_accessibility(request, submenu, user_perms, *args, **kwargs):
    return request.user.is_superuser or request.user.has_perm("lms.view_testattempt")

from django.utils.translation import gettext_lazy as trans

MENU = trans("Feedback")
IMG_SRC = "images/ui/announcement.svg"
SUBMENUS = [
    {"menu": trans("Give Feedback"), "redirect": "/feedback/give/"},
    {"menu": trans("My Feedback"), "redirect": "/feedback/my/"},
    {
        "menu": trans("All Feedback"),
        "redirect": "/feedback/all/",
        "accessibility": "feedback.sidebar.all_feedback_accessibility",
    },
]


def all_feedback_accessibility(request, submenu, user_perms, *args, **kwargs):
    return request.user.is_superuser or request.user.has_perm(
        "feedback.view_employeefeedback"
    )

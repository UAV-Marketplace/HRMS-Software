from django.utils.translation import gettext_lazy as trans

MENU = trans("PIP")
IMG_SRC = "images/ui/report.svg"
SUBMENUS = [
    {
        "menu": trans("PIP Plans"),
        "redirect": "/pip/",
        "accessibility": "pip_management.sidebar.pip_plans_accessibility",
    },
    {"menu": trans("My PIP"), "redirect": "/pip/my/"},
]


def pip_plans_accessibility(request, submenu, user_perms, *args, **kwargs):
    return request.user.is_superuser or request.user.has_perm(
        "pip_management.view_performanceimprovementplan"
    )

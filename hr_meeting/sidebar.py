from django.utils.translation import gettext_lazy as trans

MENU = trans("HR Meetings")
IMG_SRC = "images/ui/headset-solid.svg"

SUBMENUS = [
    {
        "menu": trans("Meeting Records"),
        "redirect": "/hr-meeting/view/",
    },
]

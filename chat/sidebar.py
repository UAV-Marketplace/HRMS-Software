from django.utils.translation import gettext_lazy as trans

MENU = trans("Chat")
IMG_SRC = "images/ui/at-circle.svg"

SUBMENUS = [
    {
        "menu": trans("HR Chat"),
        "redirect": "/chat/",
    },
]

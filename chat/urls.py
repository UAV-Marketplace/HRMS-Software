from django.urls import path

from chat import views

urlpatterns = [
    path("", views.chat_home, name="chat-home"),
    path("<int:conv_id>/panel/", views.chat_right_panel, name="chat-right-panel"),
    path("<int:conv_id>/poll/", views.chat_poll, name="chat-poll"),
    path("<int:conv_id>/send/", views.chat_send, name="chat-send"),
    path("conv-list/", views.chat_conv_list, name="chat-conv-list"),
    # Floating widget
    path("widget/", views.chat_widget, name="chat-widget"),
    path("widget/<int:conv_id>/", views.chat_widget_panel, name="chat-widget-panel"),
    path("unread/", views.chat_unread_count, name="chat-unread-count"),
]

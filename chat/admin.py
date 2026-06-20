from django.contrib import admin

from chat.models import ChatConversation, ChatMessage


@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = ["employee", "created_at", "last_message_at"]
    search_fields = ["employee__employee_first_name", "employee__employee_last_name"]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ["conversation", "sender", "sent_at", "is_read_by_hr", "is_read_by_employee"]
    list_filter = ["is_read_by_hr", "is_read_by_employee"]

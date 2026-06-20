from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

from employee.models import Employee


class ChatConversation(models.Model):
    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE,
        related_name="hr_chat",
        verbose_name=_("Employee"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-last_message_at"]
        verbose_name = _("Chat Conversation")
        verbose_name_plural = _("Chat Conversations")

    def __str__(self):
        return f"Chat — {self.employee}"

    def unread_for_hr(self):
        return self.messages.filter(is_read_by_hr=False).count()

    def unread_for_employee(self):
        return self.messages.filter(is_read_by_employee=False).count()

    def last_message(self):
        return self.messages.order_by("-sent_at").first()


class ChatMessage(models.Model):
    conversation = models.ForeignKey(
        ChatConversation,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name=_("Conversation"),
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_chat_messages",
        verbose_name=_("Sender"),
    )
    message = models.TextField(verbose_name=_("Message"))
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read_by_hr = models.BooleanField(default=False)
    is_read_by_employee = models.BooleanField(default=False)

    class Meta:
        ordering = ["sent_at"]
        verbose_name = _("Chat Message")
        verbose_name_plural = _("Chat Messages")

    def __str__(self):
        return f"{self.sender} — {self.message[:40]}"

    def sender_name(self):
        try:
            return self.sender.employee_get.get_full_name()
        except Exception:
            return self.sender.get_full_name() or self.sender.username

    def sender_initial(self):
        try:
            return (self.sender.employee_get.employee_first_name or "?")[0].upper()
        except Exception:
            name = self.sender.get_full_name() or self.sender.username or "?"
            return name[0].upper()

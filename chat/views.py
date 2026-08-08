import contextlib

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import models as db_models
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from notifications.signals import notify

from chat.models import ChatConversation, ChatMessage

# The only people employees are allowed to start a chat with. Each employee
# picks one of these when starting a new conversation; every conversation
# belongs to exactly one of them (see ChatConversation.recipient).
CHAT_RECIPIENT_EMAILS = ["careers@uavmarketplace.in", "info@uavmarketplace.in"]


def _get_employee(request):
    try:
        return request.user.employee_get
    except Exception:
        return None


def _is_recipient_user(request):
    """
    True if the logged-in user is one of the designated chat recipients
    (i.e. they should see the HR-side inbox, not the employee-side picker).
    """
    email = (request.user.email or "").lower()
    username = (request.user.username or "").lower()
    targets = {e.lower() for e in CHAT_RECIPIENT_EMAILS}
    return email in targets or username in targets


def get_chat_recipients():
    """
    Returns the configured recipient Users, in CHAT_RECIPIENT_EMAILS order.
    """
    condition = Q()
    for email in CHAT_RECIPIENT_EMAILS:
        condition |= Q(email__iexact=email) | Q(username__iexact=email)
    users_by_email = {}
    for user in User.objects.filter(condition):
        users_by_email[user.email.lower()] = user
        users_by_email[user.username.lower()] = user
    ordered, seen = [], set()
    for email in CHAT_RECIPIENT_EMAILS:
        user = users_by_email.get(email.lower())
        if user and user.id not in seen:
            ordered.append(user)
            seen.add(user.id)
    return ordered


def get_recipient_options(employee):
    """
    One entry per configured recipient, paired with the employee's existing
    conversation with them (if any) — used to render the "who do you want to
    message" picker with unread badges / last-message previews.
    """
    convs_by_recipient = {
        conv.recipient_id: conv
        for conv in ChatConversation.objects.filter(employee=employee)
    }
    return [
        {"user": user, "conv": convs_by_recipient.get(user.id)}
        for user in get_chat_recipients()
    ]


def _can_access_conv(request, conv):
    """
    A conversation may only be opened by its recipient or by the employee it
    belongs to — not by the other recipient, and not by an unrelated employee
    guessing a conversation id.
    """
    if conv.recipient_id == request.user.id:
        return True
    employee = _get_employee(request)
    return employee is not None and conv.employee_id == employee.id


def _mark_read_for_hr(conv):
    conv.messages.filter(is_read_by_hr=False).update(is_read_by_hr=True)


def _mark_read_for_employee(conv, user):
    conv.messages.exclude(sender=user).filter(is_read_by_employee=False).update(
        is_read_by_employee=True
    )


# ── Main page ─────────────────────────────────────────────────────────────────


@login_required
def chat_home(request):
    if _is_recipient_user(request):
        conversations = ChatConversation.objects.filter(
            recipient=request.user
        ).select_related("employee").order_by(
            db_models.F("last_message_at").desc(nulls_last=True)
        )
        return render(request, "chat/chat_hr.html", {"conversations": conversations})

    employee = _get_employee(request)
    if not employee:
        messages.error(request, _("No employee profile linked to your account."))
        return render(request, "chat/chat_employee.html", {"conv": None, "recipient_options": []})

    recipient_id = request.GET.get("to")
    if recipient_id:
        recipient = get_object_or_404(
            User, id=recipient_id, id__in=[u.id for u in get_chat_recipients()]
        )
        conv, _created = ChatConversation.objects.get_or_create(
            employee=employee, recipient=recipient
        )
        _mark_read_for_employee(conv, request.user)
        msgs_qs = conv.messages.order_by("sent_at")
        return render(
            request,
            "chat/chat_employee.html",
            {"conv": conv, "messages_qs": msgs_qs, "viewer": request.user},
        )

    return render(
        request,
        "chat/chat_employee.html",
        {"conv": None, "recipient_options": get_recipient_options(employee)},
    )


# ── HR: conversation panel ─────────────────────────────────────────────────────


@login_required
def chat_right_panel(request, conv_id):
    if not _is_recipient_user(request):
        return HttpResponse(status=403)
    conv = get_object_or_404(ChatConversation, id=conv_id, recipient=request.user)
    _mark_read_for_hr(conv)
    msgs_qs = conv.messages.order_by("sent_at")
    return render(
        request,
        "chat/partials/right_panel.html",
        {"conv": conv, "messages_qs": msgs_qs, "viewer": request.user},
    )


@login_required
def chat_conv_list(request):
    if not _is_recipient_user(request):
        return HttpResponse(status=403)
    conversations = ChatConversation.objects.filter(
        recipient=request.user
    ).select_related("employee").order_by(
        db_models.F("last_message_at").desc(nulls_last=True)
    )
    return render(
        request, "chat/partials/conv_list.html", {"conversations": conversations}
    )


# ── Shared: poll + send ────────────────────────────────────────────────────────


@login_required
def chat_poll(request, conv_id):
    conv = get_object_or_404(ChatConversation, id=conv_id)
    if not _can_access_conv(request, conv):
        return HttpResponse(status=403)
    if conv.recipient_id == request.user.id:
        _mark_read_for_hr(conv)
    else:
        _mark_read_for_employee(conv, request.user)
    msgs_qs = conv.messages.order_by("sent_at")
    return render(
        request,
        "chat/partials/messages.html",
        {"conv": conv, "messages_qs": msgs_qs, "viewer": request.user},
    )


@login_required
def chat_send(request, conv_id):
    if request.method != "POST":
        return HttpResponse(status=405)

    conv = get_object_or_404(ChatConversation, id=conv_id)
    if not _can_access_conv(request, conv):
        return HttpResponse(status=403)
    text = request.POST.get("message", "").strip()
    is_hr = conv.recipient_id == request.user.id

    if text:
        msg = ChatMessage.objects.create(
            conversation=conv,
            sender=request.user,
            message=text,
            is_read_by_hr=is_hr,
            is_read_by_employee=not is_hr,
        )
        conv.last_message_at = msg.sent_at
        conv.save(update_fields=["last_message_at"])

        with contextlib.suppress(Exception):
            if is_hr:
                notify.send(
                    request.user,
                    recipient=conv.employee.employee_user_id,
                    verb=f"{request.user.get_full_name() or request.user.username} sent you a new message.",
                    verb_ar="أرسل لك HR رسالة جديدة.",
                    verb_de="HR hat Ihnen eine neue Nachricht gesendet.",
                    verb_es="RRHH le ha enviado un nuevo mensaje.",
                    verb_fr="RH vous a envoyé un nouveau message.",
                    icon="chatbubble-outline",
                    redirect="/chat/",
                )
            else:
                employee = _get_employee(request)
                name = employee.get_full_name() if employee else request.user.username
                notify.send(
                    request.user,
                    recipient=conv.recipient,
                    verb=f"{name} sent a message in chat.",
                    verb_ar=f"أرسل {name} رسالة في الدردشة.",
                    verb_de=f"{name} hat eine Nachricht im Chat gesendet.",
                    verb_es=f"{name} envió un mensaje en el chat.",
                    verb_fr=f"{name} a envoyé un message dans le chat.",
                    icon="chatbubble-outline",
                    redirect="/chat/",
                )

    if is_hr:
        _mark_read_for_hr(conv)
    else:
        _mark_read_for_employee(conv, request.user)

    msgs_qs = conv.messages.order_by("sent_at")
    return render(
        request,
        "chat/partials/messages.html",
        {"conv": conv, "messages_qs": msgs_qs, "viewer": request.user},
    )


# ── Floating widget ────────────────────────────────────────────────────────────


@login_required
def chat_unread_count(request):
    if _is_recipient_user(request):
        count = ChatMessage.objects.filter(
            conversation__recipient=request.user, is_read_by_hr=False
        ).count()
    else:
        count = 0
        with contextlib.suppress(Exception):
            employee = request.user.employee_get
            count = ChatMessage.objects.filter(
                conversation__employee=employee, is_read_by_employee=False
            ).count()
    return render(request, "chat/widget/unread_badge.html", {"count": count})


@login_required
def chat_widget(request):
    if _is_recipient_user(request):
        conversations = ChatConversation.objects.filter(
            recipient=request.user
        ).select_related("employee").order_by(
            db_models.F("last_message_at").desc(nulls_last=True)
        )
        return render(request, "chat/widget/hr_widget.html", {"conversations": conversations})

    try:
        employee = request.user.employee_get
    except Exception:
        return HttpResponse(
            '<p style="padding:20px;text-align:center;color:#9ca3af;">No employee profile found.</p>'
        )

    recipient_id = request.GET.get("to")
    if recipient_id:
        recipient = get_object_or_404(
            User, id=recipient_id, id__in=[u.id for u in get_chat_recipients()]
        )
        conv, _created = ChatConversation.objects.get_or_create(
            employee=employee, recipient=recipient
        )
        _mark_read_for_employee(conv, request.user)
        msgs_qs = conv.messages.order_by("sent_at")
        return render(
            request,
            "chat/widget/employee_widget.html",
            {"conv": conv, "messages_qs": msgs_qs, "viewer": request.user},
        )

    return render(
        request,
        "chat/widget/employee_picker.html",
        {"recipient_options": get_recipient_options(employee)},
    )


@login_required
def chat_widget_panel(request, conv_id):
    if not _is_recipient_user(request):
        return HttpResponse(status=403)
    conv = get_object_or_404(ChatConversation, id=conv_id, recipient=request.user)
    _mark_read_for_hr(conv)
    msgs_qs = conv.messages.order_by("sent_at")
    return render(
        request,
        "chat/widget/hr_conv_panel.html",
        {"conv": conv, "messages_qs": msgs_qs, "viewer": request.user},
    )

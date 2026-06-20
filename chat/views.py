import contextlib

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import models as db_models
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from notifications.signals import notify

from chat.models import ChatConversation, ChatMessage


def _get_employee(request):
    try:
        return request.user.employee_get
    except Exception:
        return None


def _is_hr_user(request):
    return request.user.is_superuser or request.user.has_perm("base.view_dashboard")


def _mark_read_for_hr(conv):
    conv.messages.filter(is_read_by_hr=False).update(is_read_by_hr=True)


def _mark_read_for_employee(conv, user):
    conv.messages.exclude(sender=user).filter(is_read_by_employee=False).update(
        is_read_by_employee=True
    )


# ── Main page ─────────────────────────────────────────────────────────────────


@login_required
def chat_home(request):
    if _is_hr_user(request):
        conversations = ChatConversation.objects.select_related("employee").order_by(
            db_models.F("last_message_at").desc(nulls_last=True)
        )
        return render(request, "chat/chat_hr.html", {"conversations": conversations})

    employee = _get_employee(request)
    if not employee:
        messages.error(request, _("No employee profile linked to your account."))
        return render(request, "chat/chat_employee.html", {"conv": None})

    conv, _ = ChatConversation.objects.get_or_create(employee=employee)
    _mark_read_for_employee(conv, request.user)
    msgs_qs = conv.messages.order_by("sent_at")
    return render(
        request,
        "chat/chat_employee.html",
        {"conv": conv, "messages_qs": msgs_qs, "viewer": request.user},
    )


# ── HR: conversation panel ─────────────────────────────────────────────────────


@login_required
def chat_right_panel(request, conv_id):
    if not _is_hr_user(request):
        return HttpResponse(status=403)
    conv = get_object_or_404(ChatConversation, id=conv_id)
    _mark_read_for_hr(conv)
    msgs_qs = conv.messages.order_by("sent_at")
    return render(
        request,
        "chat/partials/right_panel.html",
        {"conv": conv, "messages_qs": msgs_qs, "viewer": request.user},
    )


@login_required
def chat_conv_list(request):
    if not _is_hr_user(request):
        return HttpResponse(status=403)
    conversations = ChatConversation.objects.select_related("employee").order_by(
        db_models.F("last_message_at").desc(nulls_last=True)
    )
    return render(
        request, "chat/partials/conv_list.html", {"conversations": conversations}
    )


# ── Shared: poll + send ────────────────────────────────────────────────────────


@login_required
def chat_poll(request, conv_id):
    conv = get_object_or_404(ChatConversation, id=conv_id)
    if _is_hr_user(request):
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
    text = request.POST.get("message", "").strip()
    is_hr = _is_hr_user(request)

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
                    verb="HR sent you a new message.",
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
                for hr_user in User.objects.filter(is_superuser=True).exclude(
                    id=request.user.id
                ):
                    notify.send(
                        request.user,
                        recipient=hr_user,
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
    is_hr = _is_hr_user(request)
    if is_hr:
        count = ChatMessage.objects.filter(is_read_by_hr=False).count()
    else:
        count = 0
        with contextlib.suppress(Exception):
            employee = request.user.employee_get
            conv = ChatConversation.objects.filter(employee=employee).first()
            if conv:
                count = conv.messages.filter(is_read_by_employee=False).count()
    return render(request, "chat/widget/unread_badge.html", {"count": count})


@login_required
def chat_widget(request):
    is_hr = _is_hr_user(request)
    if is_hr:
        conversations = ChatConversation.objects.select_related("employee").order_by(
            db_models.F("last_message_at").desc(nulls_last=True)
        )
        return render(request, "chat/widget/hr_widget.html", {"conversations": conversations})

    try:
        employee = request.user.employee_get
    except Exception:
        return HttpResponse(
            '<p style="padding:20px;text-align:center;color:#9ca3af;">No employee profile found.</p>'
        )

    conv, _ = ChatConversation.objects.get_or_create(employee=employee)
    _mark_read_for_employee(conv, request.user)
    msgs_qs = conv.messages.order_by("sent_at")
    return render(
        request,
        "chat/widget/employee_widget.html",
        {"conv": conv, "messages_qs": msgs_qs, "viewer": request.user},
    )


@login_required
def chat_widget_panel(request, conv_id):
    if not _is_hr_user(request):
        return HttpResponse(status=403)
    conv = get_object_or_404(ChatConversation, id=conv_id)
    _mark_read_for_hr(conv)
    msgs_qs = conv.messages.order_by("sent_at")
    return render(
        request,
        "chat/widget/hr_conv_panel.html",
        {"conv": conv, "messages_qs": msgs_qs, "viewer": request.user},
    )

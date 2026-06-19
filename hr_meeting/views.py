import contextlib

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import gettext as _
from notifications.signals import notify

from base.methods import paginator_qry
from hr_meeting.forms import HRMeetingRecordForm
from hr_meeting.models import HRMeetingRecord


@login_required
def hr_meeting_view(request):
    records = HRMeetingRecord.objects.filter(is_active=True)
    records = paginator_qry(records, request.GET.get("page", 1))
    return render(
        request,
        "hr_meeting/hr_meeting_view.html",
        {"records": records, "form": HRMeetingRecordForm()},
    )


@login_required
def hr_meeting_filter(request):
    records = HRMeetingRecord.objects.filter(is_active=True)
    if search := request.GET.get("search"):
        records = records.filter(purpose__icontains=search)
    records = paginator_qry(records, request.GET.get("page", 1))
    pd = request.GET.urlencode()
    return render(
        request,
        "hr_meeting/hr_meeting_list.html",
        {"records": records, "pd": pd},
    )


@login_required
def hr_meeting_create(request):
    form = HRMeetingRecordForm()
    if request.method == "POST":
        form = HRMeetingRecordForm(request.POST, request.FILES)
        if form.is_valid():
            record = form.save()
            for emp in record.people_involved.all():
                if emp.employee_user_id != request.user:
                    with contextlib.suppress(Exception):
                        notify.send(
                            request.user.employee_get,
                            recipient=emp.employee_user_id,
                            verb=f"You have been added to a meeting record: \"{record.purpose}\".",
                            verb_ar=f"لقد تمت إضافتك إلى سجل اجتماع: \"{record.purpose}\".",
                            verb_de=f"Sie wurden einem Besprechungsprotokoll hinzugefügt: \"{record.purpose}\".",
                            verb_es=f"Ha sido añadido a un registro de reunión: \"{record.purpose}\".",
                            verb_fr=f"Vous avez été ajouté à un relevé de réunion: \"{record.purpose}\".",
                            icon="calendar-outline",
                            redirect="/hr-meeting/view/",
                        )
            messages.success(request, _("Meeting record created successfully."))
            return HttpResponse("<script>window.location.reload();</script>")
    return render(request, "hr_meeting/hr_meeting_form.html", {"form": form})


@login_required
def hr_meeting_update(request, id):
    record = HRMeetingRecord.objects.get(id=id)
    form = HRMeetingRecordForm(instance=record)
    if request.method == "POST":
        form = HRMeetingRecordForm(request.POST, request.FILES, instance=record)
        if form.is_valid():
            record = form.save()
            for emp in record.people_involved.all():
                if emp.employee_user_id != request.user:
                    with contextlib.suppress(Exception):
                        notify.send(
                            request.user.employee_get,
                            recipient=emp.employee_user_id,
                            verb=f"A meeting record you're involved in was updated: \"{record.purpose}\".",
                            verb_ar=f"تم تحديث سجل اجتماع أنت طرف فيه: \"{record.purpose}\".",
                            verb_de=f"Ein Besprechungsprotokoll, an dem Sie beteiligt sind, wurde aktualisiert: \"{record.purpose}\".",
                            verb_es=f"Se ha actualizado un registro de reunión en el que participa: \"{record.purpose}\".",
                            verb_fr=f"Un relevé de réunion auquel vous participez a été mis à jour: \"{record.purpose}\".",
                            icon="calendar-outline",
                            redirect="/hr-meeting/view/",
                        )
            messages.success(request, _("Meeting record updated successfully."))
            return HttpResponse("<script>window.location.reload();</script>")
    return render(
        request,
        "hr_meeting/hr_meeting_form.html",
        {"form": form, "record_id": id},
    )


@login_required
def hr_meeting_delete(request, id):
    try:
        record = HRMeetingRecord.objects.get(id=id)
        record.delete()
        messages.success(request, _("Meeting record deleted successfully."))
    except HRMeetingRecord.DoesNotExist:
        messages.error(request, _("Meeting record not found."))
    records = HRMeetingRecord.objects.filter(is_active=True)
    records = paginator_qry(records, request.GET.get("page", 1))
    pd = request.GET.urlencode()
    return render(
        request,
        "hr_meeting/hr_meeting_list.html",
        {"records": records, "pd": pd},
    )

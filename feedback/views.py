import contextlib

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from notifications.signals import notify

from base.methods import paginator_qry
from feedback.forms import FeedbackForm
from feedback.models import EmployeeFeedback


def _get_employee(request):
    try:
        return request.user.employee_get
    except Exception:
        return None


@login_required
def give_feedback(request):
    employee = _get_employee(request)
    form = FeedbackForm(exclude_employee=employee)

    if request.method == "POST":
        form = FeedbackForm(request.POST, exclude_employee=employee)
        if form.is_valid():
            if not employee:
                messages.error(request, _("No employee profile linked to your account."))
                return redirect("feedback-give")
            fb = form.save(commit=False)
            fb.given_by = employee
            fb.save()
            # Notify recipient — sender is request.user (not employee_get) so the
            # notification template shows "Anonymous" instead of the giver's name.
            with contextlib.suppress(Exception):
                notify.send(
                    request.user,
                    recipient=fb.about_employee.employee_user_id,
                    verb="You have received new anonymous feedback from a colleague. Visit your Feedback section to view it.",
                    verb_ar="لقد تلقيت ملاحظات مجهولة جديدة من زميل. تفضل بزيارة قسم الملاحظات الخاص بك.",
                    verb_de="Sie haben neues anonymes Feedback von einem Kollegen erhalten. Besuchen Sie Ihren Feedback-Bereich.",
                    verb_es="Ha recibido nuevos comentarios anónimos de un colega. Visite su sección de comentarios.",
                    verb_fr="Vous avez reçu de nouveaux commentaires anonymes d'un collègue. Consultez votre section de commentaires.",
                    icon="star-outline",
                    redirect="/feedback/my/",
                )
            messages.success(request, _("Your feedback has been submitted anonymously."))
            return redirect("feedback-give")

    return render(request, "feedback/give_feedback.html", {"form": form})


@login_required
def my_feedback(request):
    employee = _get_employee(request)
    if not employee:
        messages.error(request, _("No employee profile linked to your account."))
        return render(request, "feedback/my_feedback.html", {
            "feedbacks": [], "stats": None,
        })

    qs = EmployeeFeedback.objects.filter(about_employee=employee)
    stats = qs.aggregate(avg_rating=Avg("rating"), total=Count("id"))
    feedbacks = paginator_qry(qs, request.GET.get("page", 1))
    return render(request, "feedback/my_feedback.html", {
        "feedbacks": feedbacks,
        "stats": stats,
    })


@login_required
def all_feedback(request):
    qs = EmployeeFeedback.objects.select_related(
        "given_by", "about_employee"
    )
    search = request.GET.get("search", "").strip()
    if search:
        qs = qs.filter(
            about_employee__employee_first_name__icontains=search
        ) | qs.filter(
            about_employee__employee_last_name__icontains=search
        ) | qs.filter(
            given_by__employee_first_name__icontains=search
        ) | qs.filter(
            given_by__employee_last_name__icontains=search
        )
    feedbacks = paginator_qry(qs, request.GET.get("page", 1))
    return render(request, "feedback/all_feedback.html", {
        "feedbacks": feedbacks,
        "pd": request.GET.urlencode(),
        "search": search,
    })

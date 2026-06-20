import contextlib

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from notifications.signals import notify

from base.methods import paginator_qry
from pip_management.forms import PIPForm, PIPGoalForm, PIPReviewForm
from pip_management.models import (
    PIPGoal,
    PIPProgressReview,
    PerformanceImprovementPlan,
)


def _get_employee(request):
    try:
        return request.user.employee_get
    except Exception:
        return None


# ── HR / Admin ────────────────────────────────────────────────────────────────

@login_required
def pip_list(request):
    plans = PerformanceImprovementPlan.objects.select_related(
        "employee"
    ).filter(is_active=True)
    plans = paginator_qry(plans, request.GET.get("page", 1))
    return render(request, "pip_management/pip_list.html", {
        "plans": plans,
        "pd": request.GET.urlencode(),
        "status_choices": PerformanceImprovementPlan.STATUS_CHOICES,
    })


@login_required
def pip_filter(request):
    plans = PerformanceImprovementPlan.objects.select_related(
        "employee"
    ).filter(is_active=True)
    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip()
    if search:
        plans = plans.filter(
            employee__employee_first_name__icontains=search
        ) | plans.filter(
            employee__employee_last_name__icontains=search
        )
    if status:
        plans = plans.filter(status=status)
    plans = paginator_qry(plans, request.GET.get("page", 1))
    return render(request, "pip_management/pip_table.html", {
        "plans": plans,
        "pd": request.GET.urlencode(),
    })


@login_required
def pip_create(request):
    form = PIPForm()
    if request.method == "POST":
        form = PIPForm(request.POST)
        if form.is_valid():
            pip = form.save()
            with contextlib.suppress(Exception):
                notify.send(
                    request.user.employee_get,
                    recipient=pip.employee.employee_user_id,
                    verb=f"A Performance Improvement Plan has been created for you. Please review it with your HR.",
                    verb_ar="تم إنشاء خطة تحسين الأداء لك. يرجى مراجعتها مع HR.",
                    verb_de="Ein Leistungsverbesserungsplan wurde für Sie erstellt. Bitte besprechen Sie ihn mit HR.",
                    verb_es="Se ha creado un Plan de Mejora del Rendimiento para usted. Por favor revíselo con RRHH.",
                    verb_fr="Un Plan d'Amélioration des Performances a été créé pour vous. Veuillez le consulter avec les RH.",
                    icon="document-text-outline",
                    redirect=f"/pip/my/",
                )
            messages.success(request, _("PIP created successfully."))
            return HttpResponse("<script>window.location.reload();</script>")
    return render(request, "pip_management/pip_form.html", {"form": form})


@login_required
def pip_update(request, pip_id):
    pip = get_object_or_404(PerformanceImprovementPlan, id=pip_id)
    old_status = pip.status
    form = PIPForm(instance=pip)
    if request.method == "POST":
        form = PIPForm(request.POST, instance=pip)
        if form.is_valid():
            pip = form.save()
            if old_status != pip.status:
                with contextlib.suppress(Exception):
                    notify.send(
                        request.user.employee_get,
                        recipient=pip.employee.employee_user_id,
                        verb=f"Your Performance Improvement Plan status has been updated to: {pip.get_status_display()}.",
                        verb_ar=f"تم تحديث حالة خطة تحسين الأداء الخاصة بك إلى: {pip.get_status_display()}.",
                        verb_de=f"Ihr Leistungsverbesserungsplan wurde aktualisiert auf: {pip.get_status_display()}.",
                        verb_es=f"El estado de su Plan de Mejora del Rendimiento se ha actualizado a: {pip.get_status_display()}.",
                        verb_fr=f"Le statut de votre Plan d'Amélioration des Performances a été mis à jour: {pip.get_status_display()}.",
                        icon="document-text-outline",
                        redirect="/pip/my/",
                    )
            messages.success(request, _("PIP updated successfully."))
            return HttpResponse("<script>window.location.reload();</script>")
    return render(request, "pip_management/pip_form.html", {"form": form, "pip": pip})


@login_required
def pip_delete(request, pip_id):
    pip = get_object_or_404(PerformanceImprovementPlan, id=pip_id)
    pip.delete()
    messages.success(request, _("PIP deleted."))
    plans = PerformanceImprovementPlan.objects.select_related(
        "employee"
    ).filter(is_active=True)
    plans = paginator_qry(plans, 1)
    return render(request, "pip_management/pip_table.html", {
        "plans": plans,
        "pd": "",
    })


@login_required
def pip_detail(request, pip_id):
    pip = get_object_or_404(PerformanceImprovementPlan, id=pip_id)
    goals = pip.goals.all()
    reviews = pip.reviews.filter(is_active=True).order_by("-review_date")
    return render(request, "pip_management/pip_detail.html", {
        "pip": pip,
        "goals": goals,
        "reviews": reviews,
        "goal_form": PIPGoalForm(),
        "review_form": PIPReviewForm(),
    })


# ── Goals ─────────────────────────────────────────────────────────────────────

@login_required
def pip_goal_add(request, pip_id):
    pip = get_object_or_404(PerformanceImprovementPlan, id=pip_id)
    if request.method == "POST":
        form = PIPGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.pip = pip
            goal.save()
            messages.success(request, _("Goal added."))
    return redirect("pip-detail", pip_id=pip_id)


@login_required
def pip_goal_toggle(request, goal_id):
    goal = get_object_or_404(PIPGoal, id=goal_id)
    goal.is_achieved = not goal.is_achieved
    goal.save()
    return redirect("pip-detail", pip_id=goal.pip_id)


@login_required
def pip_goal_delete(request, goal_id):
    goal = get_object_or_404(PIPGoal, id=goal_id)
    pip_id = goal.pip_id
    goal.delete()
    messages.success(request, _("Goal removed."))
    return redirect("pip-detail", pip_id=pip_id)


# ── Progress Reviews ──────────────────────────────────────────────────────────

@login_required
def pip_review_add(request, pip_id):
    pip = get_object_or_404(PerformanceImprovementPlan, id=pip_id)
    if request.method == "POST":
        form = PIPReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.pip = pip
            review.reviewed_by = _get_employee(request)
            review.save()
            with contextlib.suppress(Exception):
                notify.send(
                    request.user.employee_get,
                    recipient=pip.employee.employee_user_id,
                    verb="A progress review has been added to your Performance Improvement Plan.",
                    verb_ar="تمت إضافة مراجعة تقدم إلى خطة تحسين الأداء الخاصة بك.",
                    verb_de="Eine Fortschrittsüberprüfung wurde zu Ihrem Leistungsverbesserungsplan hinzugefügt.",
                    verb_es="Se ha añadido una revisión de progreso a su Plan de Mejora del Rendimiento.",
                    verb_fr="Un examen de progression a été ajouté à votre Plan d'Amélioration des Performances.",
                    icon="clipboard-outline",
                    redirect="/pip/my/",
                )
            messages.success(request, _("Progress review added."))
    return redirect("pip-detail", pip_id=pip_id)


# ── Employee ──────────────────────────────────────────────────────────────────

@login_required
def my_pip(request):
    employee = _get_employee(request)
    if not employee:
        messages.error(request, _("No employee profile linked to your account."))
        return render(request, "pip_management/my_pip.html", {"plans": []})
    plans = (
        PerformanceImprovementPlan.objects.filter(employee=employee, is_active=True)
        .prefetch_related("goals", "reviews")
        .order_by("-created_at")
    )
    return render(request, "pip_management/my_pip.html", {"plans": plans})

import contextlib

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from notifications.signals import notify

from base.methods import paginator_qry
from lms.forms import CourseAssignForm, CourseForm, QuestionForm, TestConfigForm
from lms.models import (
    Course,
    CourseAssignment,
    LMSQuestion,
    LMSQuestionOption,
    TestAnswer,
    TestAttempt,
    TestConfiguration,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _get_employee(request):
    try:
        return request.user.employee_get
    except Exception:
        return None


def _auto_fail(attempt):
    attempt.is_submitted = True
    attempt.completed_at = timezone.now()
    attempt.score = 0
    attempt.passed = False
    attempt.is_suspicious = True
    attempt.save()


# ── HR / Admin – Course management ───────────────────────────────────────────

@login_required
def lms_courses(request):
    courses = Course.objects.filter(is_active=True)
    courses = paginator_qry(courses, request.GET.get("page", 1))
    return render(request, "lms/lms_courses.html", {
        "courses": courses,
        "pd": request.GET.urlencode(),
    })


@login_required
def lms_course_filter(request):
    courses = Course.objects.filter(is_active=True)
    if search := request.GET.get("search"):
        courses = courses.filter(title__icontains=search)
    courses = paginator_qry(courses, request.GET.get("page", 1))
    return render(request, "lms/course_list.html", {
        "courses": courses,
        "pd": request.GET.urlencode(),
    })


@login_required
def lms_course_create(request):
    form = CourseForm()
    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save()
            TestConfiguration.objects.get_or_create(
                course=course,
                defaults={"duration_minutes": 30, "pass_percentage": 70, "max_attempts": 3},
            )
            messages.success(request, _("Course created successfully."))
            return HttpResponse("<script>window.location.reload();</script>")
    return render(request, "lms/course_form.html", {"form": form})


@login_required
def lms_course_update(request, id):
    course = get_object_or_404(Course, id=id)
    form = CourseForm(instance=course)
    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, _("Course updated."))
            return HttpResponse("<script>window.location.reload();</script>")
    return render(request, "lms/course_form.html", {"form": form, "course_id": id})


@login_required
def lms_course_delete(request, id):
    course = get_object_or_404(Course, id=id)
    course.delete()
    messages.success(request, _("Course deleted."))
    courses = Course.objects.filter(is_active=True)
    courses = paginator_qry(courses, 1)
    return render(request, "lms/course_list.html", {"courses": courses, "pd": ""})


@login_required
def lms_course_assign(request, id):
    course = get_object_or_404(Course, id=id)
    form = CourseAssignForm()
    if request.method == "POST":
        form = CourseAssignForm(request.POST)
        if form.is_valid():
            count = 0
            for emp in form.cleaned_data["employees"]:
                assignment, created = CourseAssignment.objects.get_or_create(
                    course=course, employee=emp
                )
                if created:
                    count += 1
                    with contextlib.suppress(Exception):
                        notify.send(
                            request.user.employee_get,
                            recipient=emp.employee_user_id,
                            verb=f"A new course has been assigned to you: \"{course.title}\". Log in to start learning!",
                            verb_ar=f"تم تعيين دورة جديدة لك: \"{course.title}\". سجّل دخولك لبدء التعلم!",
                            verb_de=f"Ihnen wurde ein neuer Kurs zugewiesen: \"{course.title}\". Melden Sie sich an, um zu lernen!",
                            verb_es=f"Se le ha asignado un nuevo curso: \"{course.title}\". ¡Inicie sesión para comenzar a aprender!",
                            verb_fr=f"Un nouveau cours vous a été assigné: \"{course.title}\". Connectez-vous pour commencer à apprendre!",
                            icon="book-outline",
                            redirect="/lms/my-courses/",
                        )
            messages.success(
                request,
                _("{n} employee(s) assigned to \"{c}\".").format(n=count, c=course.title),
            )
            return HttpResponse("<script>window.location.reload();</script>")
    return render(request, "lms/assign_form.html", {"form": form, "course": course})


# ── HR / Admin – Question management ─────────────────────────────────────────

@login_required
def lms_question_management(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    questions = course.questions.filter(is_active=True).prefetch_related("options")
    return render(request, "lms/question_management.html", {
        "course": course,
        "questions": questions,
    })


@login_required
def lms_question_create(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    form = QuestionForm()
    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            question = LMSQuestion.objects.create(
                course=course, question_text=cd["question_text"]
            )
            correct = cd["correct_option"]
            for key in ("a", "b", "c", "d"):
                LMSQuestionOption.objects.create(
                    question=question,
                    option_text=cd[f"option_{key}"],
                    is_correct=(key == correct),
                )
            messages.success(request, _("Question added."))
            return HttpResponse("<script>window.location.reload();</script>")
    return render(request, "lms/question_form.html", {"form": form, "course": course})


@login_required
def lms_question_update(request, question_id):
    question = get_object_or_404(LMSQuestion, id=question_id)
    options = list(question.options.order_by("id"))
    letter_map = {0: "a", 1: "b", 2: "c", 3: "d"}
    correct_letter = next(
        (letter_map[i] for i, o in enumerate(options) if o.is_correct), "a"
    )
    initial = {
        "question_text": question.question_text,
        "correct_option": correct_letter,
    }
    for i, key in enumerate(("a", "b", "c", "d")):
        initial[f"option_{key}"] = options[i].option_text if i < len(options) else ""

    form = QuestionForm(initial=initial)
    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            question.question_text = cd["question_text"]
            question.save()
            question.options.all().delete()
            correct = cd["correct_option"]
            for key in ("a", "b", "c", "d"):
                LMSQuestionOption.objects.create(
                    question=question,
                    option_text=cd[f"option_{key}"],
                    is_correct=(key == correct),
                )
            messages.success(request, _("Question updated."))
            return HttpResponse("<script>window.location.reload();</script>")
    return render(request, "lms/question_form.html", {
        "form": form,
        "question": question,
        "course": question.course,
    })


@login_required
def lms_question_delete(request, question_id):
    question = get_object_or_404(LMSQuestion, id=question_id)
    course_id = question.course_id
    question.delete()
    messages.success(request, _("Question deleted."))
    return redirect("lms-question-management", course_id=course_id)


# ── HR / Admin – Test configuration & results ─────────────────────────────────

@login_required
def lms_test_config(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    config, _created = TestConfiguration.objects.get_or_create(
        course=course,
        defaults={"duration_minutes": 30, "pass_percentage": 70, "max_attempts": 3},
    )
    form = TestConfigForm(instance=config)
    if request.method == "POST":
        form = TestConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, _("Test configuration saved."))
            return HttpResponse("<script>window.location.reload();</script>")
    return render(request, "lms/test_config_form.html", {"form": form, "course": course})


@login_required
def lms_results(request):
    attempts = TestAttempt.objects.select_related(
        "assignment__employee", "assignment__course"
    ).order_by("-started_at")
    if search := request.GET.get("search"):
        attempts = attempts.filter(
            assignment__employee__employee_first_name__icontains=search
        ) | attempts.filter(assignment__course__title__icontains=search)
    attempts = paginator_qry(attempts, request.GET.get("page", 1))
    return render(request, "lms/lms_results.html", {
        "attempts": attempts,
        "pd": request.GET.urlencode(),
    })


# ── Employee views ────────────────────────────────────────────────────────────

@login_required
def my_courses(request):
    employee = _get_employee(request)
    if not employee:
        messages.error(request, _("No employee profile linked to your account."))
        return render(request, "lms/my_courses.html", {"assignments_data": []})
    raw_assignments = (
        CourseAssignment.objects.filter(employee=employee, is_active=True)
        .select_related("course", "course__test_config")
        .prefetch_related("test_attempts__answers")
    )
    assignments_data = []
    for asgn in raw_assignments:
        config = getattr(asgn.course, "test_config", None)
        max_attempts = config.max_attempts if config else 0
        all_attempts = list(asgn.test_attempts.order_by("-started_at"))
        submitted = [a for a in all_attempts if a.is_submitted]
        attempts_taken = len(submitted)
        latest_attempt = all_attempts[0] if all_attempts else None
        passed_attempt = next((a for a in all_attempts if a.passed), None)
        has_active = latest_attempt and not latest_attempt.is_submitted
        can_start = bool(config) and (attempts_taken < max_attempts) and not asgn.is_completed
        assignments_data.append({
            "asgn": asgn,
            "config": config,
            "attempts_taken": attempts_taken,
            "max_attempts": max_attempts,
            "latest_attempt": latest_attempt,
            "passed_attempt": passed_attempt,
            "has_active": has_active,
            "can_start": can_start,
        })
    return render(request, "lms/my_courses.html", {"assignments_data": assignments_data})


@login_required
def start_test(request, assignment_id):
    assignment = get_object_or_404(CourseAssignment, id=assignment_id)
    employee = _get_employee(request)
    if not employee or assignment.employee != employee:
        messages.error(request, _("Access denied."))
        return redirect("lms-my-courses")

    course = assignment.course
    config = getattr(course, "test_config", None)
    max_attempts = config.max_attempts if config else 3

    if not course.questions.filter(is_active=True).exists():
        messages.error(request, _("No test questions available for this course yet."))
        return redirect("lms-my-courses")

    if assignment.attempts_taken() >= max_attempts:
        messages.error(request, _("Maximum attempts reached."))
        return redirect("lms-my-courses")

    # Resume an active attempt if still within time
    active = assignment.test_attempts.filter(is_submitted=False).first()
    if active:
        elapsed = (timezone.now() - active.started_at).total_seconds()
        limit = (config.duration_minutes * 60) if config else 1800
        if elapsed > limit:
            _auto_fail(active)
        else:
            return redirect("lms-test-interface", attempt_id=active.id)

    attempt = TestAttempt.objects.create(
        assignment=assignment,
        attempt_number=assignment.test_attempts.count() + 1,
    )
    return redirect("lms-test-interface", attempt_id=attempt.id)


@login_required
def test_interface(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id)
    employee = _get_employee(request)
    if not employee or attempt.assignment.employee != employee:
        messages.error(request, _("Access denied."))
        return redirect("lms-my-courses")

    if attempt.is_submitted:
        return redirect("lms-test-result", attempt_id=attempt.id)

    course = attempt.assignment.course
    config = getattr(course, "test_config", None)
    duration_seconds = (config.duration_minutes * 60) if config else 1800
    elapsed = (timezone.now() - attempt.started_at).total_seconds()
    time_remaining = max(0, int(duration_seconds - elapsed))

    if time_remaining == 0:
        _auto_fail(attempt)
        return redirect("lms-test-result", attempt_id=attempt.id)

    questions = (
        course.questions.filter(is_active=True)
        .prefetch_related("options")
        .order_by("order", "id")
    )
    return render(request, "lms/test_interface.html", {
        "attempt": attempt,
        "course": course,
        "questions": questions,
        "config": config,
        "time_remaining": time_remaining,
    })


@login_required
def submit_test(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id)
    employee = _get_employee(request)
    if not employee or attempt.assignment.employee != employee:
        return JsonResponse({"error": "Access denied"}, status=403)

    if attempt.is_submitted:
        return redirect("lms-test-result", attempt_id=attempt.id)

    course = attempt.assignment.course
    config = getattr(course, "test_config", None)

    # Grace-period check (30 seconds over the limit is allowed for network delay)
    if config:
        elapsed = (timezone.now() - attempt.started_at).total_seconds()
        if elapsed > config.duration_minutes * 60 + 30:
            _auto_fail(attempt)
            return redirect("lms-test-result", attempt_id=attempt.id)

    questions = course.questions.filter(is_active=True)
    total = questions.count()
    correct_count = 0

    for question in questions:
        opt_id = request.POST.get(f"q_{question.id}")
        selected = None
        if opt_id:
            try:
                selected = LMSQuestionOption.objects.get(id=opt_id, question=question)
            except LMSQuestionOption.DoesNotExist:
                pass
        TestAnswer.objects.update_or_create(
            attempt=attempt,
            question=question,
            defaults={"selected_option": selected},
        )
        if selected and selected.is_correct:
            correct_count += 1

    score = round((correct_count / total * 100) if total else 0, 2)
    pass_pct = config.pass_percentage if config else 70

    attempt.is_submitted = True
    attempt.completed_at = timezone.now()
    attempt.total_questions = total
    attempt.correct_answers = correct_count
    attempt.score = score
    attempt.passed = score >= pass_pct
    attempt.save()

    if attempt.passed:
        asgn = attempt.assignment
        asgn.is_completed = True
        asgn.completed_at = timezone.now()
        asgn.save()

    return redirect("lms-test-result", attempt_id=attempt.id)


@login_required
def test_result(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id)
    employee = _get_employee(request)
    is_owner = employee and attempt.assignment.employee == employee
    is_hr = request.user.has_perm("lms.view_testattempt")
    if not is_owner and not is_hr:
        messages.error(request, _("Access denied."))
        return redirect("lms-my-courses")

    answers = attempt.answers.select_related(
        "question", "selected_option"
    ).prefetch_related("question__options").order_by("question__order", "question__id")
    config = getattr(attempt.assignment.course, "test_config", None)
    return render(request, "lms/test_result.html", {
        "attempt": attempt,
        "answers": answers,
        "config": config,
    })


@login_required
def record_tab_switch(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id)
    if not attempt.is_submitted:
        attempt.tab_switch_count += 1
        if attempt.tab_switch_count >= 3:
            attempt.is_suspicious = True
        attempt.save()
    return JsonResponse({"tab_switches": attempt.tab_switch_count})


@login_required
def lms_manage_assignments(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    assignments = (
        CourseAssignment.objects.filter(course=course)
        .select_related("employee")
        .order_by("employee__employee_first_name", "employee__employee_last_name")
    )
    return render(request, "lms/manage_assignments.html", {
        "course": course,
        "assignments": assignments,
    })


@login_required
def lms_course_unassign(request, assignment_id):
    assignment = get_object_or_404(CourseAssignment, id=assignment_id)
    course = assignment.course
    emp_name = str(assignment.employee)
    assignment.delete()
    messages.success(
        request,
        _("{emp} has been unassigned from \"{c}\".").format(emp=emp_name, c=course.title),
    )
    assignments = (
        CourseAssignment.objects.filter(course=course)
        .select_related("employee")
        .order_by("employee__employee_first_name", "employee__employee_last_name")
    )
    return render(request, "lms/manage_assignments.html", {
        "course": course,
        "assignments": assignments,
    })

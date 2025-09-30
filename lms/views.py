from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from .models import *
from .forms import UserEditForm, CourseMaterialForm, AssignmentForm, StudentSubmissionForm, GradeSubmissionForm


def access_denied(request):
    return render(request, 'lms/access_denied.html')


def is_professor(user):
    return hasattr(user, 'professor')


def is_student(user):
    return hasattr(user, 'student')


def home(request):
    return render(request, 'lms/home.html')


def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                try:
                    Student.objects.get(user=user)
                    return redirect('student_dashboard')
                except Student.DoesNotExist:
                    pass

                try:
                    Professor.objects.get(user=user)
                    return redirect('professor_dashboard')
                except Professor.DoesNotExist:
                    pass

                return redirect('/admin/')
    else:
        form = AuthenticationForm()

    return render(request, 'lms/login.html', {'form': form})


def custom_logout(request):
    logout(request)
    return redirect('home')


@login_required
@user_passes_test(is_student, login_url='access_denied')
def student_dashboard(request):
    student = get_object_or_404(Student, user=request.user)
    enrollments = Enrollment.objects.filter(student=student).select_related(
        'class_enrolled', 'class_enrolled__course', 'class_enrolled__professor'
    )

    current_semester = "Весна 2024"

    current_enrollments = enrollments.filter(class_enrolled__semester=current_semester)
    completed_enrollments = enrollments.exclude(class_enrolled__semester=current_semester)

    total_credits = 0
    weighted_sum = 0

    grade_points = {
        'A': 4.0, 'B': 3.0, 'C': 2.0, 'D': 1.0, 'F': 0.0,
        'A-': 3.7, 'B+': 3.3, 'B-': 2.7, 'C+': 2.3, 'C-': 1.7,
        'D+': 1.3, 'D-': 0.7
    }

    for enrollment in enrollments:
        if enrollment.grade and enrollment.grade in grade_points:
            course_credits = enrollment.class_enrolled.course.credits
            total_credits += course_credits
            weighted_sum += grade_points[enrollment.grade] * course_credits

    gpa = weighted_sum / total_credits if total_credits > 0 else 0

    return render(request, 'lms/student_dashboard.html', {
        'student': student,
        'current_enrollments': current_enrollments,
        'completed_enrollments': completed_enrollments,
        'gpa': round(gpa, 2)
    })


@login_required
@user_passes_test(is_professor, login_url='access_denied')
def professor_dashboard(request):
    professor = get_object_or_404(Professor, user=request.user)
    classes = Class.objects.filter(professor=professor)
    return render(request, 'lms/professor_dashboard.html', {
        'professor': professor,
        'classes': classes
    })


@login_required
def course_catalog(request):
    courses = Course.objects.select_related('department', 'department__faculty').all()

    faculty_filter = request.GET.get('faculty')
    if faculty_filter:
        courses = courses.filter(department__faculty_id=faculty_filter)

    department_filter = request.GET.get('department')
    if department_filter:
        courses = courses.filter(department_id=department_filter)

    search_query = request.GET.get('search')
    if search_query:
        courses = courses.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query)
        )

    paginator = Paginator(courses, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    faculties = Faculty.objects.all()
    departments = Department.objects.all()

    return render(request, 'lms/course_catalog.html', {
        'courses': page_obj,
        'faculties': faculties,
        'departments': departments
    })


@login_required
def class_detail(request, class_id):
    class_obj = get_object_or_404(Class, id=class_id)
    enrollments = Enrollment.objects.filter(class_enrolled=class_obj)

    is_enrolled = False
    is_professor = False
    is_student = False

    if hasattr(request.user, 'student'):
        student = request.user.student
        is_student = True
        is_enrolled = Enrollment.objects.filter(student=student, class_enrolled=class_obj).exists()

    if hasattr(request.user, 'professor'):
        professor = request.user.professor
        is_professor = (class_obj.professor == professor)

    materials = CourseMaterial.objects.filter(class_obj=class_obj)

    return render(request, 'lms/class_detail.html', {
        'class': class_obj,
        'enrollments': enrollments,
        'materials': materials,
        'is_enrolled': is_enrolled,
        'is_professor': is_professor,
        'is_student': is_student
    })


@login_required
@user_passes_test(is_student, login_url='access_denied')
def enroll_course(request, class_id):
    student = get_object_or_404(Student, user=request.user)
    class_obj = get_object_or_404(Class, id=class_id)

    if Enrollment.objects.filter(student=student, class_enrolled=class_obj).exists():
        messages.warning(request, "Ви вже записані на цей курс.")
    else:
        Enrollment.objects.create(student=student, class_enrolled=class_obj)
        messages.success(request, f"Ви успішно записались на курс {class_obj.course.name}.")

    return HttpResponseRedirect(reverse('class_detail', args=[class_id]))


@login_required
@user_passes_test(is_professor, login_url='access_denied')
def professor_grades(request, class_id):
    professor = get_object_or_404(Professor, user=request.user)
    class_obj = get_object_or_404(Class, id=class_id, professor=professor)
    enrollments = Enrollment.objects.filter(class_enrolled=class_obj)

    if request.method == 'POST':
        for enrollment in enrollments:
            grade_field = f'grade_{enrollment.id}'
            if grade_field in request.POST:
                enrollment.grade = request.POST[grade_field]
                enrollment.save()
        messages.success(request, 'Оцінки успішно оновлено.')
        return redirect('professor_grades', class_id=class_id)

    return render(request, 'lms/professor_grades.html', {
        'class_obj': class_obj,
        'enrollments': enrollments,
    })


@login_required
@user_passes_test(is_professor, login_url='access_denied')
def upload_course_material(request, class_id):
    professor = get_object_or_404(Professor, user=request.user)
    class_obj = get_object_or_404(Class, id=class_id, professor=professor)

    if request.method == 'POST':
        form = CourseMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.class_obj = class_obj
            material.save()
            messages.success(request, 'Матеріал успішно завантажено.')
            return redirect('class_detail', class_id=class_id)
    else:
        form = CourseMaterialForm()

    return render(request, 'lms/upload_material.html', {
        'form': form,
        'class_obj': class_obj,
    })


@login_required
def delete_course_material(request, material_id):
    try:
        professor = Professor.objects.get(user=request.user)
        material = get_object_or_404(CourseMaterial, id=material_id)

        if material.class_obj.professor != professor:
            messages.error(request, "Ви не маєте прав для видалення цього матеріалу.")
            return redirect('class_detail', class_id=material.class_obj.id)

        class_id = material.class_obj.id
        material.delete()
        messages.success(request, "Матеріал успішно видалено.")
        return redirect('class_detail', class_id=class_id)

    except Professor.DoesNotExist:
        messages.error(request, "Доступ заборонено. Тільки викладачі можуть видаляти матеріали.")
        return redirect('home')


@login_required
def schedule(request):
    try:
        if hasattr(request.user, 'student'):
            student = request.user.student
            enrollments = Enrollment.objects.filter(student=student)
            classes = [enrollment.class_enrolled for enrollment in enrollments]
            schedules = Schedule.objects.filter(class_obj__in=classes).order_by('day_of_week', 'start_time')
            user_type = 'student'
        elif hasattr(request.user, 'professor'):
            professor = request.user.professor
            classes = Class.objects.filter(professor=professor)
            schedules = Schedule.objects.filter(class_obj__in=classes).order_by('day_of_week', 'start_time')
            user_type = 'professor'
        else:
            return render(request, 'lms/access_denied.html')

        schedule_by_day = {}
        DAYS_OF_WEEK_DISPLAY = {
            'MON': 'Понеділок',
            'TUE': 'Вівторок',
            'WED': 'Середа',
            'THU': 'Четвер',
            'FRI': 'П\'ятниця',
            'SAT': 'Субота'
        }

        for schedule in schedules:
            day_display = DAYS_OF_WEEK_DISPLAY.get(schedule.day_of_week, schedule.day_of_week)
            if day_display not in schedule_by_day:
                schedule_by_day[day_display] = []
            schedule_by_day[day_display].append(schedule)

        return render(request, 'lms/schedule.html', {
            'schedule_by_day': schedule_by_day,
            'user_type': user_type
        })
    except Exception as e:
        return render(request, 'lms/access_denied.html')


@login_required
def profile(request):
    user = request.user
    context = {'user': user}

    if hasattr(user, 'student'):
        context['profile'] = user.student
        context['user_type'] = 'student'
    elif hasattr(user, 'professor'):
        context['profile'] = user.professor
        context['user_type'] = 'professor'
    else:
        context['user_type'] = 'other'

    return render(request, 'lms/profile.html', context)


@login_required
def edit_profile(request):
    user = request.user

    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профіль успішно оновлено.')
            return redirect('profile')
    else:
        form = UserEditForm(instance=user)

    return render(request, 'lms/edit_profile.html', {'form': form})


@login_required
def create_assignment(request, class_id):
    try:
        professor = Professor.objects.get(user=request.user)
        class_obj = get_object_or_404(Class, id=class_id, professor=professor)

        if request.method == 'POST':
            form = AssignmentForm(request.POST)
            if form.is_valid():
                assignment = form.save(commit=False)
                assignment.class_obj = class_obj
                assignment.save()
                messages.success(request, 'Завдання успішно створено.')
                return redirect('class_assignments', class_id=class_id)
        else:
            form = AssignmentForm()

        return render(request, 'lms/create_assignment.html', {
            'form': form,
            'class_obj': class_obj,
        })
    except Professor.DoesNotExist:
        return render(request, 'lms/access_denied.html')


@login_required
def class_assignments(request, class_id):
    class_obj = get_object_or_404(Class, id=class_id)
    assignments = Assignment.objects.filter(class_obj=class_obj)

    is_professor = False
    try:
        professor = Professor.objects.get(user=request.user)
        is_professor = (class_obj.professor == professor)
    except Professor.DoesNotExist:
        pass

    is_student = False
    student_submissions = {}
    try:
        student = Student.objects.get(user=request.user)
        is_student = True
        submissions = StudentSubmission.objects.filter(
            student=student,
            assignment__class_obj=class_obj
        ).select_related('assignment')
        student_submissions = {submission.assignment.id: submission for submission in submissions}
    except Student.DoesNotExist:
        pass

    return render(request, 'lms/class_assignments.html', {
        'class_obj': class_obj,
        'assignments': assignments,
        'is_professor': is_professor,
        'is_student': is_student,
        'student_submissions': student_submissions,
    })


@login_required
def submit_assignment(request, assignment_id):
    try:
        student = Student.objects.get(user=request.user)
        assignment = get_object_or_404(Assignment, id=assignment_id)

        if not Enrollment.objects.filter(student=student, class_enrolled=assignment.class_obj).exists():
            messages.error(request, "Ви не записані на цей курс.")
            return redirect('class_assignments', class_id=assignment.class_obj.id)

        existing_submission = StudentSubmission.objects.filter(student=student, assignment=assignment).first()

        if request.method == 'POST':
            form = StudentSubmissionForm(request.POST, request.FILES, instance=existing_submission)
            if form.is_valid():
                submission = form.save(commit=False)
                submission.student = student
                submission.assignment = assignment
                submission.save()
                messages.success(request, 'Роботу успішно здано.')
                return redirect('class_assignments', class_id=assignment.class_obj.id)
        else:
            form = StudentSubmissionForm(instance=existing_submission)

        return render(request, 'lms/submit_assignment.html', {
            'form': form,
            'assignment': assignment,
            'existing_submission': existing_submission,
        })
    except Student.DoesNotExist:
        messages.error(request, "Доступ заборонено. Тільки студенти можуть здавати роботи.")
        return redirect('home')


@login_required
def view_submissions(request, assignment_id):
    try:
        professor = Professor.objects.get(user=request.user)
        assignment = get_object_or_404(Assignment, id=assignment_id, class_obj__professor=professor)
        submissions = StudentSubmission.objects.filter(assignment=assignment).select_related('student', 'student__user')

        return render(request, 'lms/view_submissions.html', {
            'assignment': assignment,
            'submissions': submissions,
        })
    except Professor.DoesNotExist:
        return render(request, 'lms/access_denied.html')


@login_required
def grade_submission(request, submission_id):
    try:
        professor = Professor.objects.get(user=request.user)
        submission = get_object_or_404(StudentSubmission, id=submission_id, assignment__class_obj__professor=professor)

        if request.method == 'POST':
            form = GradeSubmissionForm(request.POST, instance=submission)
            if form.is_valid():
                submission = form.save(commit=False)
                submission.graded_at = timezone.now()
                submission.save()
                messages.success(request, 'Оцінку успішно виставлено.')
                return redirect('view_submissions', assignment_id=submission.assignment.id)
        else:
            form = GradeSubmissionForm(instance=submission)

        return render(request, 'lms/grade_submission.html', {
            'form': form,
            'submission': submission,
        })
    except Professor.DoesNotExist:
        return render(request, 'lms/access_denied.html')
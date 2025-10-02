from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.db import models
from django.db.models import Avg, Count, Q
from django.contrib import messages
from .models import (
    Student, Professor, Class, Enrollment, CourseMaterial,
    Assignment, StudentSubmission, Course, Faculty, Department
)
from .forms import (
    UserEditForm, CourseMaterialForm, AssignmentForm,
    StudentSubmissionForm, GradeSubmissionForm
)


def home(request):
    """Главная страница"""
    context = {}

    if request.user.is_authenticated:
        try:
            if hasattr(request.user, 'student'):
                student = request.user.student
                enrollments = Enrollment.objects.filter(student=student).select_related('class_enrolled')
                context['enrolled_courses_count'] = enrollments.count()

                # Получаем активные задания
                assignments_count = Assignment.objects.filter(
                    class_obj__in=[enrollment.class_enrolled for enrollment in enrollments]
                ).count()
                context['assignments_count'] = assignments_count

            elif hasattr(request.user, 'professor'):
                professor = request.user.professor
                professor_classes = Class.objects.filter(professor=professor)
                context['enrolled_courses_count'] = professor_classes.count()

                # Получаем задания, созданные преподавателем
                assignments_count = Assignment.objects.filter(
                    class_obj__in=professor_classes
                ).count()
                context['assignments_count'] = assignments_count

                # Получаем количество отправленных работ
                submissions_count = StudentSubmission.objects.filter(
                    assignment__class_obj__in=professor_classes
                ).count()
                context['submissions_count'] = submissions_count

        except (Student.DoesNotExist, Professor.DoesNotExist):
            pass

    return render(request, 'lms/home.html', context)


def custom_logout(request):
    """Кастомный выход из системы"""
    logout(request)
    return redirect('home')


@login_required
def edit_profile(request):
    """Редактирование профиля пользователя"""
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = UserEditForm(instance=request.user)

    return render(request, 'lms/edit_profile.html', {'form': form})


@login_required
def student_dashboard(request):
    """Панель управления студента"""
    try:
        student = request.user.student
    except Student.DoesNotExist:
        return HttpResponseForbidden("Доступ запрещен")

    # Получаем зачисления студента
    enrollments = Enrollment.objects.filter(student=student).select_related('class_enrolled')
    enrolled_classes = [enrollment.class_enrolled for enrollment in enrollments]

    # Получаем задания для классов студента
    assignments = Assignment.objects.filter(class_obj__in=enrolled_classes)

    # Получаем отправленные задания
    submitted_assignments = StudentSubmission.objects.filter(
        student=student,
        assignment__in=assignments
    ).values_list('assignment', flat=True)

    context = {
        'student': student,
        'enrolled_courses': enrolled_classes,
        'recent_assignments': assignments.order_by('-due_date')[:5],
        'submitted_assignments': submitted_assignments,
        'pending_assignments': assignments.exclude(id__in=submitted_assignments),
    }

    return render(request, 'lms/student_dashboard.html', context)


@login_required
def professor_dashboard(request):
    """Панель управления преподавателя"""
    try:
        professor = request.user.professor
    except Professor.DoesNotExist:
        return HttpResponseForbidden("Доступ запрещен")

    # Получаем классы преподавателя
    professor_classes = Class.objects.filter(professor=professor)

    # Получаем задания
    assignments = Assignment.objects.filter(class_obj__in=professor_classes)

    # Получаем отправленные работы
    submissions = StudentSubmission.objects.filter(assignment__in=assignments)

    context = {
        'professor': professor,
        'classes': professor_classes,
        'assignments_count': assignments.count(),
        'submissions_count': submissions.count(),
        'pending_submissions_count': submissions.filter(grade__isnull=True).count(),
    }

    return render(request, 'lms/professor_dashboard.html', context)


@login_required
def professor_grades(request):
    """Управління оцінками для викладача"""
    try:
        professor = request.user.professor
    except Professor.DoesNotExist:
        return HttpResponseForbidden("Доступ заборонено")

    # Отримуємо курси викладача
    courses = Class.objects.filter(professor=professor).select_related('course')

    course_data = []
    for course_class in courses:
        course = course_class.course

        # Отримуємо студентів курсу
        enrollments = Enrollment.objects.filter(class_enrolled=course_class).select_related('student__user')

        students_data = []
        for enrollment in enrollments:
            student = enrollment.student

            # Отримуємо завдання та роботи студента
            assignments = Assignment.objects.filter(class_obj=course_class)
            submissions = StudentSubmission.objects.filter(
                student=student,
                assignment__in=assignments
            )

            # Статистика
            submitted_count = submissions.count()
            total_assignments = assignments.count()
            completion_percentage = (submitted_count / total_assignments * 100) if total_assignments > 0 else 0

            graded_submissions = submissions.exclude(grade__isnull=True)
            if graded_submissions.exists():
                average_grade = graded_submissions.aggregate(Avg('grade'))['grade__avg']
                max_points_sum = sum(sub.assignment.max_points for sub in graded_submissions)
                achieved_points = sum(sub.grade for sub in graded_submissions)

                if max_points_sum > 0:
                    percentage = (achieved_points / max_points_sum) * 100
                    final_grade = calculate_final_grade(percentage)
                    final_grade_class = get_grade_class(percentage)
                else:
                    final_grade = "Н/Д"
                    final_grade_class = "secondary"
            else:
                average_grade = None
                final_grade = "Н/Д"
                final_grade_class = "secondary"

            students_data.append({
                'student': student,
                'submitted_count': submitted_count,
                'total_assignments': total_assignments,
                'completion_percentage': completion_percentage,
                'average_grade': average_grade,
                'final_grade': final_grade,
                'final_grade_class': final_grade_class
            })

        course_data.append({
            'id': course.id,
            'name': course.name,
            'students': students_data
        })

    context = {
        'courses': course_data
    }

    return render(request, 'lms/professor_grades.html', context)


@login_required
def student_course_grades(request, course_id, student_id):
    """Детальные оценки студента по конкретному курсу"""
    try:
        professor = request.user.professor
    except Professor.DoesNotExist:
        return HttpResponseForbidden("Доступ запрещен")

    course = get_object_or_404(Course, id=course_id)
    student = get_object_or_404(Student, id=student_id)

    # Проверяем, что преподаватель ведет этот курс
    course_class = get_object_or_404(Class, course=course, professor=professor)

    # Получаем все задания курса и работы студента
    assignments = Assignment.objects.filter(class_obj=course_class)
    submissions = StudentSubmission.objects.filter(
        student=student,
        assignment__in=assignments
    ).select_related('assignment')

    context = {
        'course': course,
        'student': student,
        'assignments': assignments,
        'submissions': submissions,
    }

    return render(request, 'lms/student_course_grades.html', context)


@login_required
def set_final_grade(request):
    """Установка финальной оценки за курс"""
    if request.method == 'POST':
        try:
            professor = request.user.professor
            student_id = request.POST.get('student_id')
            course_id = request.POST.get('course_id')
            final_grade = request.POST.get('final_grade')
            comments = request.POST.get('comments', '')

            student = get_object_or_404(Student, id=student_id)
            course = get_object_or_404(Course, id=course_id)

            # Проверяем, что преподаватель ведет этот курс
            course_class = get_object_or_404(Class, course=course, professor=professor)

            # Здесь можно сохранить финальную оценку в модель Enrollment
            enrollment = get_object_or_404(Enrollment, student=student, class_enrolled=course_class)
            enrollment.grade = final_grade
            enrollment.save()

            messages.success(request, f'Фінальну оцінку для {student.user.get_full_name()} успішно встановлено.')

        except Exception as e:
            messages.error(request, f'Помилка при встановленні оцінки: {str(e)}')

    return redirect('professor_grades')


@login_required
def class_list(request):
    """Список всех классов"""
    if hasattr(request.user, 'student'):
        enrollments = Enrollment.objects.filter(student=request.user.student)
        classes = [enrollment.class_enrolled for enrollment in enrollments]
    elif hasattr(request.user, 'professor'):
        classes = Class.objects.filter(professor=request.user.professor)
    else:
        classes = Class.objects.all()

    return render(request, 'lms/class_list.html', {'classes': classes})


@login_required
def class_detail(request, class_id):
    """Детальная информация о классе"""
    class_obj = get_object_or_404(Class, id=class_id)

    # Проверка доступа
    if hasattr(request.user, 'student'):
        if not Enrollment.objects.filter(student=request.user.student, class_enrolled=class_obj).exists():
            return HttpResponseForbidden("Доступ запрещен")

    context = {
        'class_obj': class_obj,
        'materials': CourseMaterial.objects.filter(class_obj=class_obj),
        'assignments': Assignment.objects.filter(class_obj=class_obj),
    }

    return render(request, 'lms/class_detail.html', context)


@login_required
def class_materials(request, class_id):
    """Материалы класса"""
    class_obj = get_object_or_404(Class, id=class_id)

    # Проверка доступа
    if hasattr(request.user, 'student'):
        if not Enrollment.objects.filter(student=request.user.student, class_enrolled=class_obj).exists():
            return HttpResponseForbidden("Доступ запрещен")

    materials = CourseMaterial.objects.filter(class_obj=class_obj)

    return render(request, 'lms/class_materials.html', {
        'class_obj': class_obj,
        'materials': materials
    })


@login_required
def upload_course_material(request, class_id):
    """Загрузка материала курса"""
    class_obj = get_object_or_404(Class, id=class_id)

    # Только преподаватель может загружать материалы
    if not hasattr(request.user, 'professor') or class_obj.professor != request.user.professor:
        return HttpResponseForbidden("Доступ запрещен")

    if request.method == 'POST':
        form = CourseMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.class_obj = class_obj
            material.save()
            return redirect('class_materials', class_id=class_id)
    else:
        form = CourseMaterialForm()

    return render(request, 'lms/upload_material.html', {
        'form': form,
        'class_obj': class_obj
    })


@login_required
def class_assignments(request, class_id):
    """Список заданий класса"""
    class_obj = get_object_or_404(Class, id=class_id)

    # Проверка доступа
    if hasattr(request.user, 'student'):
        if not Enrollment.objects.filter(student=request.user.student, class_enrolled=class_obj).exists():
            return HttpResponseForbidden("Доступ запрещен")

    assignments = Assignment.objects.filter(class_obj=class_obj)

    # Для студентов получаем отправленные задания
    submitted_assignments = []
    if hasattr(request.user, 'student'):
        submitted_assignments = StudentSubmission.objects.filter(
            student=request.user.student,
            assignment__in=assignments
        ).values_list('assignment_id', flat=True)

    return render(request, 'lms/class_assignments.html', {
        'class_obj': class_obj,
        'assignments': assignments,
        'submitted_assignments': submitted_assignments
    })


@login_required
def create_assignment(request, class_id):
    """Создание нового задания"""
    class_obj = get_object_or_404(Class, id=class_id)

    # Только преподаватель может создавать задания
    if not hasattr(request.user, 'professor') or class_obj.professor != request.user.professor:
        return HttpResponseForbidden("Доступ запрещен")

    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.class_obj = class_obj
            assignment.save()
            return redirect('class_assignments', class_id=class_id)
    else:
        form = AssignmentForm()

    return render(request, 'lms/create_assignment.html', {
        'form': form,
        'class_obj': class_obj
    })


@login_required
def assignment_detail(request, assignment_id):
    """Детальная информация о задании"""
    assignment = get_object_or_404(Assignment, id=assignment_id)

    # Проверка доступа
    if hasattr(request.user, 'student'):
        if not Enrollment.objects.filter(
                student=request.user.student,
                class_enrolled=assignment.class_obj
        ).exists():
            return HttpResponseForbidden("Доступ запрещен")

    # Для студентов получаем их отправку
    student_submission = None
    if hasattr(request.user, 'student'):
        try:
            student_submission = StudentSubmission.objects.get(
                student=request.user.student,
                assignment=assignment
            )
        except StudentSubmission.DoesNotExist:
            pass

    context = {
        'assignment': assignment,
        'student_submission': student_submission,
    }

    return render(request, 'lms/assignment_detail.html', context)


@login_required
def submit_assignment(request, assignment_id):
    """Отправка задания студентом"""
    assignment = get_object_or_404(Assignment, id=assignment_id)

    # Только студент может отправлять задания
    try:
        student = request.user.student
    except Student.DoesNotExist:
        return HttpResponseForbidden("Доступ запрещен")

    # Проверка, что студент записан на курс
    if not Enrollment.objects.filter(
            student=student,
            class_enrolled=assignment.class_obj
    ).exists():
        return HttpResponseForbidden("Доступ запрещен")

    # Проверка, что задание уже не отправлено
    try:
        existing_submission = StudentSubmission.objects.get(
            student=student,
            assignment=assignment
        )
        # Если отправка уже существует, перенаправляем на детали
        return redirect('assignment_detail', assignment_id=assignment_id)
    except StudentSubmission.DoesNotExist:
        pass

    if request.method == 'POST':
        form = StudentSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.student = student
            submission.assignment = assignment
            submission.save()
            return redirect('assignment_detail', assignment_id=assignment_id)
    else:
        form = StudentSubmissionForm()

    return render(request, 'lms/submit_assignment.html', {
        'form': form,
        'assignment': assignment
    })


@login_required
def assignment_submissions(request, assignment_id):
    """Список отправленных работ для задания"""
    assignment = get_object_or_404(Assignment, id=assignment_id)

    # Только преподаватель курса может просматривать отправки
    if not hasattr(request.user, 'professor') or assignment.class_obj.professor != request.user.professor:
        return HttpResponseForbidden("Доступ запрещен")

    submissions = StudentSubmission.objects.filter(assignment=assignment).select_related('student')

    return render(request, 'lms/assignment_submissions.html', {
        'assignment': assignment,
        'submissions': submissions
    })


@login_required
def grade_submission(request, submission_id):
    """Оценка отправленной работы"""
    submission = get_object_or_404(StudentSubmission, id=submission_id)

    # Только преподаватель курса может оценивать работы
    if not hasattr(request.user, 'professor') or submission.assignment.class_obj.professor != request.user.professor:
        return HttpResponseForbidden("Доступ запрещен")

    if request.method == 'POST':
        form = GradeSubmissionForm(request.POST, instance=submission)
        if form.is_valid():
            graded_submission = form.save(commit=False)
            graded_submission.graded_at = timezone.now()
            graded_submission.save()
            return redirect('assignment_submissions', assignment_id=submission.assignment.id)
    else:
        form = GradeSubmissionForm(instance=submission)

    return render(request, 'lms/grade_submission.html', {
        'form': form,
        'submission': submission
    })


@login_required
def student_courses(request):
    """Курсы студента"""
    try:
        student = request.user.student
    except Student.DoesNotExist:
        return HttpResponseForbidden("Доступ запрещен")

    enrollments = Enrollment.objects.filter(student=student).select_related('class_enrolled')

    return render(request, 'lms/student_courses.html', {
        'enrollments': enrollments
    })


@login_required
def student_assignments(request):
    """Задания студента"""
    try:
        student = request.user.student
    except Student.DoesNotExist:
        return HttpResponseForbidden("Доступ запрещен")

    # Получаем классы студента
    enrollments = Enrollment.objects.filter(student=student)
    class_ids = [enrollment.class_enrolled.id for enrollment in enrollments]

    # Получаем задания для этих классов
    assignments = Assignment.objects.filter(class_obj_id__in=class_ids).select_related('class_obj__course')

    # Получаем отправленные задания и создаем словарь для быстрого доступа
    submitted_assignments = StudentSubmission.objects.filter(
        student=student,
        assignment__in=assignments
    ).select_related('assignment')

    # Создаем словарь для быстрого доступа к отправкам по ID задания
    submission_dict = {}
    for submission in submitted_assignments:
        submission_dict[submission.assignment_id] = submission

    # Создаем список данных для отображения
    assignment_data = []
    for assignment in assignments:
        submission = submission_dict.get(assignment.id)
        assignment_data.append({
            'assignment': assignment,
            'submission': submission,
            'is_submitted': submission is not None,
            'is_graded': submission and submission.grade is not None,
            'grade_display': f"{submission.grade}/{assignment.max_points}" if submission and submission.grade else None,
            'percentage': (submission.grade / assignment.max_points * 100) if submission and submission.grade else None,
        })

    # Статистика
    total_assignments = assignments.count()
    submitted_count = len([a for a in assignment_data if a['is_submitted']])
    graded_count = len([a for a in assignment_data if a['is_graded']])
    pending_count = total_assignments - submitted_count

    context = {
        'assignment_data': assignment_data,
        'total_assignments': total_assignments,
        'submitted_count': submitted_count,
        'graded_count': graded_count,
        'pending_count': pending_count,
        'completion_rate': (submitted_count / total_assignments * 100) if total_assignments > 0 else 0,
    }

    return render(request, 'lms/student_assignments.html', context)


@login_required
def student_grades(request):
    """Оцінки студента"""
    try:
        student = request.user.student
    except Student.DoesNotExist:
        return HttpResponseForbidden("Доступ заборонено")

    # Отримуємо всі відправлені роботи студента
    submissions = StudentSubmission.objects.filter(student=student).select_related(
        'assignment__class_obj__course'
    ).order_by('-submission_date')

    # Розраховуємо статистику
    total_submissions = submissions.count()
    graded_submissions = submissions.exclude(grade__isnull=True)

    if graded_submissions.exists():
        average_grade = graded_submissions.aggregate(Avg('grade'))['grade__avg']
        # Розраховуємо процент успішних робіт (оцінка >= 60%)
        successful_submissions = graded_submissions.filter(
            grade__gte=models.F('assignment__max_points') * 0.6
        ).count()
        success_rate = (successful_submissions / total_submissions * 100) if total_submissions > 0 else 0
    else:
        average_grade = 0
        success_rate = 0

    pending_grades = submissions.filter(grade__isnull=True).count()

    # Розраховуємо процент для кожного submission
    graded_submissions_list = []
    for submission in submissions:
        if submission.grade and submission.assignment.max_points:
            percentage = (submission.grade / submission.assignment.max_points) * 100
        else:
            percentage = None

        graded_submissions_list.append({
            'submission': submission,
            'percentage': percentage,
            'grade_class': get_grade_class(percentage) if percentage else 'secondary'
        })

    # Отримуємо оцінки за курсами
    course_grades = calculate_course_grades(student)

    context = {
        'submissions': graded_submissions_list,
        'course_grades': course_grades,
        'total_submissions': total_submissions,
        'average_grade': round(average_grade, 1) if average_grade else 0,
        'success_rate': round(success_rate, 1) if success_rate else 0,
        'pending_grades': pending_grades,
        'graded_count': graded_submissions.count(),
    }

    return render(request, 'lms/student_grades.html', context)


def calculate_course_grades(student):
    """Розраховує оцінки за курсами для студента"""
    course_grades = []

    # Отримуємо всі курси студента
    enrollments = Enrollment.objects.filter(student=student).select_related(
        'class_enrolled__course'
    )

    for enrollment in enrollments:
        course = enrollment.class_enrolled.course

        # Отримуємо всі завдання для цього курсу
        assignments = Assignment.objects.filter(class_obj__course=course)

        # Отримуємо всі роботи студента для цього курсу
        course_submissions = StudentSubmission.objects.filter(
            student=student,
            assignment__in=assignments
        )

        # Розраховуємо середню оцінку
        graded_submissions = course_submissions.exclude(grade__isnull=True)
        if graded_submissions.exists():
            average_grade = graded_submissions.aggregate(Avg('grade'))['grade__avg']
            max_points_sum = sum(sub.assignment.max_points for sub in graded_submissions)
            achieved_points = sum(sub.grade for sub in graded_submissions)

            if max_points_sum > 0:
                percentage = (achieved_points / max_points_sum) * 100
                final_grade = calculate_final_grade(percentage)
            else:
                final_grade = "Н/Д"
                percentage = 0
        else:
            final_grade = "Н/Д"
            percentage = 0

        # Визначаємо статус
        if percentage >= 60:
            status = "Зараховано"
            status_class = "success"
        elif percentage > 0:
            status = "Не зараховано"
            status_class = "danger"
        else:
            status = "В процесі"
            status_class = "warning"

        course_grades.append({
            'course': course,
            'final_grade': final_grade,
            'percentage': percentage,
            'status': status,
            'status_class': status_class,
            'grade_class': get_grade_class(percentage)
        })

    return course_grades


def calculate_final_grade(percentage):
    """Конвертує процент у буквенну оцінку"""
    if percentage >= 90:
        return "A"
    elif percentage >= 80:
        return "B"
    elif percentage >= 70:
        return "C"
    elif percentage >= 60:
        return "D"
    else:
        return "F"


def get_grade_class(percentage):
    """Возвращает CSS класс для оценки на основе процента"""
    if percentage >= 90:
        return 'success'
    elif percentage >= 80:
        return 'primary'
    elif percentage >= 70:
        return 'info'
    elif percentage >= 60:
        return 'warning'
    else:
        return 'danger'
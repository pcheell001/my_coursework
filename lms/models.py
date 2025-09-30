from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class Faculty(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("назва"))
    description = models.TextField(blank=True, verbose_name=_("опис"))

    class Meta:
        verbose_name = _("факультет")
        verbose_name_plural = _("факультети")

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("назва"))
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, verbose_name=_("факультет"))

    class Meta:
        verbose_name = _("кафедра")
        verbose_name_plural = _("кафедри")

    def __str__(self):
        return self.name


class Course(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("назва"))
    code = models.CharField(max_length=10, unique=True, verbose_name=_("код"))
    description = models.TextField(verbose_name=_("опис"))
    credits = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name=_("кредити")
    )
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name=_("кафедра"))

    class Meta:
        verbose_name = _("курс")
        verbose_name_plural = _("курси")

    def __str__(self):
        return f"{self.code} - {self.name}"


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("користувач"))
    student_id = models.CharField(max_length=10, unique=True, verbose_name=_("ID студента"))
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, verbose_name=_("факультет"))
    enrollment_date = models.DateField(verbose_name=_("дата вступу"))

    class Meta:
        verbose_name = _("студент")
        verbose_name_plural = _("студенти")

    def __str__(self):
        return f"{self.student_id} - {self.user.get_full_name()}"


class Professor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("користувач"))
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name=_("кафедра"))
    office = models.CharField(max_length=50, verbose_name=_("офіс"))

    class Meta:
        verbose_name = _("викладач")
        verbose_name_plural = _("викладачі")

    def __str__(self):
        return self.user.get_full_name()


class Class(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name=_("курс"))
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE, verbose_name=_("викладач"))
    semester = models.CharField(max_length=20, verbose_name=_("семестр"))
    schedule = models.CharField(max_length=100, verbose_name=_("розклад"))
    classroom = models.CharField(max_length=50, verbose_name=_("аудиторія"))

    class Meta:
        verbose_name = _("заняття")
        verbose_name_plural = _("заняття")

    def __str__(self):
        return f"{self.course.code} - {self.semester}"


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name=_("студент"))
    class_enrolled = models.ForeignKey(Class, on_delete=models.CASCADE, verbose_name=_("заняття"))
    enrollment_date = models.DateField(auto_now_add=True, verbose_name=_("дата запису"))
    grade = models.CharField(max_length=2, blank=True, null=True, verbose_name=_("оцінка"))

    class Meta:
        unique_together = ('student', 'class_enrolled')
        verbose_name = _("запис")
        verbose_name_plural = _("записи")

    def __str__(self):
        return f"{self.student} - {self.class_enrolled}"


class CourseMaterial(models.Model):
    title = models.CharField(max_length=200, verbose_name=_("Назва матеріалу"))
    description = models.TextField(blank=True, verbose_name=_("Опис"))
    file = models.FileField(upload_to='course_materials/', verbose_name=_("Файл"))
    uploaded_at = models.DateTimeField(auto_now_add=True)
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, verbose_name=_("Заняття"))

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Матеріал курсу")
        verbose_name_plural = _("Матеріали курсу")


class Schedule(models.Model):
    DAYS_OF_WEEK = [
        ('MON', _('Понеділок')),
        ('TUE', _('Вівторок')),
        ('WED', _('Середа')),
        ('THU', _('Четвер')),
        ('FRI', _('П\'ятниця')),
        ('SAT', _('Субота')),
    ]

    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        verbose_name=_("заняття"),
        related_name='class_schedules'
    )
    day_of_week = models.CharField(max_length=3, choices=DAYS_OF_WEEK, verbose_name=_("день тижня"))
    start_time = models.TimeField(verbose_name=_("час початку"))
    end_time = models.TimeField(verbose_name=_("час закінчення"))
    classroom = models.CharField(max_length=50, verbose_name=_("аудиторія"))

    class Meta:
        verbose_name = _("розклад")
        verbose_name_plural = _("розклади")

    def __str__(self):
        return f"{self.class_obj.course.code} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


class Assignment(models.Model):
    ASSIGNMENT_TYPES = [
        ('LAB', 'Лабораторна робота'),
        ('HW', 'Домашнє завдання'),
        ('PROJECT', 'Проект'),
        ('ESSAY', 'Ессе'),
    ]

    title = models.CharField(max_length=200, verbose_name="Назва завдання")
    description = models.TextField(verbose_name="Опис завдання")
    assignment_type = models.CharField(max_length=10, choices=ASSIGNMENT_TYPES, default='LAB',
                                       verbose_name="Тип завдання")
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, verbose_name="Заняття")
    due_date = models.DateTimeField(verbose_name="Термін здачі")
    max_points = models.IntegerField(default=100, verbose_name="Максимальний бал")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.class_obj.course.name}"

    class Meta:
        verbose_name = "Завдання"
        verbose_name_plural = "Завдання"


class StudentSubmission(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="Студент")
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, verbose_name="Завдання")
    file = models.FileField(upload_to='student_submissions/', verbose_name="Файл роботи")
    submission_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата здачі")
    comment = models.TextField(blank=True, verbose_name="Коментар студента")
    grade = models.IntegerField(null=True, blank=True, verbose_name="Оцінка")
    teacher_feedback = models.TextField(blank=True, verbose_name="Відгук викладача")
    graded_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата оцінювання")

    def is_late(self):
        return self.submission_date > self.assignment.due_date

    def get_grade_percentage(self):
        if self.grade and self.assignment.max_points:
            return (self.grade / self.assignment.max_points) * 100
        return None

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.assignment.title}"

    class Meta:
        verbose_name = "Робота студента"
        verbose_name_plural = "Роботи студентів"
        unique_together = ('student', 'assignment')
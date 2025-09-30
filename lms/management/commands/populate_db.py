from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from lms.models import *
from django.utils import timezone


class Command(BaseCommand):
    help = 'Populate database with sample data'

    def handle(self, *args, **options):
        # Перевіряємо, чи вже існують дані
        if Faculty.objects.exists():
            self.stdout.write(self.style.WARNING('Дані вже існують. Видаліть існуючі дані або очистіть базу даних.'))
            return

        # Створення факультетів
        faculty1 = Faculty.objects.create(name="Факультет комп'ютерних наук",
                                          description="Факультет комп'ютерних наук та кібербезпеки")
        faculty2 = Faculty.objects.create(name="Факультет економіки", description="Факультет економіки та менеджменту")
        faculty3 = Faculty.objects.create(name="Філологічний факультет",
                                          description="Факультет іноземних мов та літератури")

        # Створення кафедр
        dept1 = Department.objects.create(name="Кафедра програмного забезпечення", faculty=faculty1)
        dept2 = Department.objects.create(name="Кафедра кібербезпеки", faculty=faculty1)
        dept3 = Department.objects.create(name="Кафедра фінансів", faculty=faculty2)
        dept4 = Department.objects.create(name="Кафедра англійської філології", faculty=faculty3)

        # Створення курсів
        course1 = Course.objects.create(
            name="Програмування на Python",
            code="PY101",
            description="Основи програмування на мові Python",
            credits=5,
            department=dept1
        )

        course2 = Course.objects.create(
            name="Веб-програмування",
            code="WEB202",
            description="Розробка веб-додатків з використанням Django",
            credits=6,
            department=dept1
        )

        course3 = Course.objects.create(
            name="Кібербезпека",
            code="CS404",
            description="Основи кібербезпеки та захисту даних",
            credits=4,
            department=dept2
        )

        course4 = Course.objects.create(
            name="Фінансовий менеджмент",
            code="FM303",
            description="Основи управління фінансами",
            credits=5,
            department=dept3
        )

        course5 = Course.objects.create(
            name="Англійська мова",
            code="ENG101",
            description="Практичний курс англійської мови",
            credits=3,
            department=dept4
        )

        # Створення користувачів - викладачів
        prof1_user, created = User.objects.get_or_create(
            username='professor1',
            defaults={
                'email': 'professor1@example.com',
                'first_name': 'Олена',
                'last_name': 'Іванова'
            }
        )
        prof1_user.set_password('professor123')
        prof1_user.save()

        prof2_user, created = User.objects.get_or_create(
            username='professor2',
            defaults={
                'email': 'professor2@example.com',
                'first_name': 'Андрій',
                'last_name': 'Петров'
            }
        )
        prof2_user.set_password('professor123')
        prof2_user.save()

        prof3_user, created = User.objects.get_or_create(
            username='professor3',
            defaults={
                'email': 'professor3@example.com',
                'first_name': 'Марія',
                'last_name': 'Сидоренко'
            }
        )
        prof3_user.set_password('professor123')
        prof3_user.save()

        # Створення користувачів - студентів
        student1_user, created = User.objects.get_or_create(
            username='student1',
            defaults={
                'email': 'student1@example.com',
                'first_name': 'Іван',
                'last_name': 'Петренко'
            }
        )
        student1_user.set_password('student123')
        student1_user.save()

        student2_user, created = User.objects.get_or_create(
            username='student2',
            defaults={
                'email': 'student2@example.com',
                'first_name': 'Марія',
                'last_name': 'Коваленко'
            }
        )
        student2_user.set_password('student123')
        student2_user.save()

        student3_user, created = User.objects.get_or_create(
            username='student3',
            defaults={
                'email': 'student3@example.com',
                'first_name': 'Олексій',
                'last_name': 'Мельник'
            }
        )
        student3_user.set_password('student123')
        student3_user.save()

        student4_user, created = User.objects.get_or_create(
            username='student4',
            defaults={
                'email': 'student4@example.com',
                'first_name': 'Анна',
                'last_name': 'Шевченко'
            }
        )
        student4_user.set_password('student123')
        student4_user.save()

        # Створення профілів викладачів
        professor1, created = Professor.objects.get_or_create(
            user=prof1_user,
            defaults={
                'department': dept1,
                'office': "Ауд. 305"
            }
        )

        professor2, created = Professor.objects.get_or_create(
            user=prof2_user,
            defaults={
                'department': dept2,
                'office': "Ауд. 412"
            }
        )

        professor3, created = Professor.objects.get_or_create(
            user=prof3_user,
            defaults={
                'department': dept4,
                'office': "Ауд. 215"
            }
        )

        # Створення профілів студентів
        student1, created = Student.objects.get_or_create(
            user=student1_user,
            defaults={
                'student_id': "S12345",
                'faculty': faculty1,
                'enrollment_date': timezone.now().date()
            }
        )

        student2, created = Student.objects.get_or_create(
            user=student2_user,
            defaults={
                'student_id': "S12346",
                'faculty': faculty1,
                'enrollment_date': timezone.now().date()
            }
        )

        student3, created = Student.objects.get_or_create(
            user=student3_user,
            defaults={
                'student_id': "S12347",
                'faculty': faculty2,
                'enrollment_date': timezone.now().date()
            }
        )

        student4, created = Student.objects.get_or_create(
            user=student4_user,
            defaults={
                'student_id': "S12348",
                'faculty': faculty3,
                'enrollment_date': timezone.now().date()
            }
        )

        # Створення занять
        class1, created = Class.objects.get_or_create(
            course=course1,
            professor=professor1,
            defaults={
                'semester': "Весна 2024",
                'schedule': "Пн 10:00-11:30, Ср 10:00-11:30",
                'classroom': "Ауд. 101"
            }
        )

        class2, created = Class.objects.get_or_create(
            course=course2,
            professor=professor1,
            defaults={
                'semester': "Весна 2024",
                'schedule': "Вт 14:00-15:30, Чт 14:00-15:30",
                'classroom': "Ауд. 102"
            }
        )

        class3, created = Class.objects.get_or_create(
            course=course3,
            professor=professor2,
            defaults={
                'semester': "Весна 2024",
                'schedule': "Пн 12:00-13:30, Ср 12:00-13:30",
                'classroom': "Ауд. 103"
            }
        )

        class4, created = Class.objects.get_or_create(
            course=course5,
            professor=professor3,
            defaults={
                'semester': "Весна 2024",
                'schedule': "Пт 10:00-12:30",
                'classroom': "Ауд. 201"
            }
        )

        # Запис студентів на курси
        Enrollment.objects.get_or_create(student=student1, class_enrolled=class1, defaults={'grade': "A"})
        Enrollment.objects.get_or_create(student=student1, class_enrolled=class2, defaults={'grade': "B"})
        Enrollment.objects.get_or_create(student=student2, class_enrolled=class1)
        Enrollment.objects.get_or_create(student=student2, class_enrolled=class3)
        Enrollment.objects.get_or_create(student=student4, class_enrolled=class4, defaults={'grade': "A"})

        self.stdout.write(self.style.SUCCESS('Успішно заповнено базу даних тестовими даними!'))
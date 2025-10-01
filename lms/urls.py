from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # Аутентификация
    path('login/', auth_views.LoginView.as_view(template_name='lms/login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),  # ЗАМЕНИЛИ НА КАСТОМНЫЙ
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    # Dashboard
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('professor/dashboard/', views.professor_dashboard, name='professor_dashboard'),

    # Курсы и классы
    path('classes/', views.class_list, name='class_list'),
    path('class/<int:class_id>/', views.class_detail, name='class_detail'),
    path('class/<int:class_id>/materials/', views.class_materials, name='class_materials'),
    path('class/<int:class_id>/materials/upload/', views.upload_course_material, name='upload_course_material'),

    # Задания
    path('class/<int:class_id>/assignments/', views.class_assignments, name='class_assignments'),
    path('class/<int:class_id>/assignments/create/', views.create_assignment, name='create_assignment'),
    path('assignment/<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('assignment/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('assignment/<int:assignment_id>/submissions/', views.assignment_submissions, name='assignment_submissions'),
    path('submission/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),

    # Студенческие маршруты
    path('student/courses/', views.student_courses, name='student_courses'),
    path('student/assignments/', views.student_assignments, name='student_assignments'),
    path('student/grades/', views.student_grades, name='student_grades'),
]
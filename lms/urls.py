from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('professor/dashboard/', views.professor_dashboard, name='professor_dashboard'),
    path('courses/', views.course_catalog, name='course_catalog'),
    path('class/<int:class_id>/', views.class_detail, name='class_detail'),
    path('class/<int:class_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('login/', views.custom_login, name='custom_login'),
    path('logout/', views.custom_logout, name='custom_logout'),
    path('class/<int:class_id>/grades/', views.professor_grades, name='professor_grades'),
    path('class/<int:class_id>/upload_material/', views.upload_course_material, name='upload_material'),
    path('material/<int:material_id>/delete/', views.delete_course_material, name='delete_material'),
    path('schedule/', views.schedule, name='schedule'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('class/<int:class_id>/assignments/', views.class_assignments, name='class_assignments'),
    path('class/<int:class_id>/assignments/create/', views.create_assignment, name='create_assignment'),
    path('assignment/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('assignment/<int:assignment_id>/submissions/', views.view_submissions, name='view_submissions'),
    path('submission/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),
]
from django.contrib import admin
from .models import *

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'faculty')
    list_filter = ('faculty',)
    search_fields = ('name', 'faculty__name')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'credits', 'department')
    list_filter = ('department', 'credits')
    search_fields = ('code', 'name')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'user', 'faculty', 'enrollment_date')
    list_filter = ('faculty', 'enrollment_date')
    search_fields = ('student_id', 'user__first_name', 'user__last_name')

@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'office')
    list_filter = ('department',)
    search_fields = ('user__first_name', 'user__last_name')

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('course', 'professor', 'semester', 'schedule', 'classroom')
    list_filter = ('semester', 'course__department')
    search_fields = ('course__code', 'course__name', 'professor__user__first_name')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'class_enrolled', 'enrollment_date', 'grade')
    list_filter = ('class_enrolled__semester', 'grade')
    search_fields = ('student__student_id', 'student__user__first_name', 'class_enrolled__course__code')

@admin.register(CourseMaterial)
class CourseMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'class_obj', 'uploaded_at')
    list_filter = ('class_obj', 'uploaded_at')
    search_fields = ('title', 'description')

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('class_obj', 'day_of_week', 'start_time', 'end_time', 'classroom')
    list_filter = ('day_of_week', 'class_obj')
    search_fields = ('class_obj__course__name', 'classroom')
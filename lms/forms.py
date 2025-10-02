from django import forms
from django.contrib.auth.models import User
from .models import CourseMaterial, Assignment, StudentSubmission


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': 'Ім\'я',
            'last_name': 'Прізвище',
            'email': 'Електронна пошта'
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ця електронна адреса вже використовується")
        return email


class CourseMaterialForm(forms.ModelForm):
    class Meta:
        model = CourseMaterial
        fields = ['title', 'description', 'file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введіть назву матеріалу'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Введіть опис матеріалу (необов\'язково)',
                'rows': 4
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'title': 'Назва матеріалу',
            'description': 'Опис',
            'file': 'Файл'
        }


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'assignment_type', 'description', 'due_date', 'max_points', 'assignment_file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введіть назву завдання'}),
            'assignment_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Введіть опис завдання', 'rows': 4}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'max_points': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': 0.5}),
            'assignment_file': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': 'Назва завдання',
            'assignment_type': 'Тип завдання',
            'description': 'Опис',
            'due_date': 'Термін здачі',
            'max_points': 'Максимальний бал',
            'assignment_file': 'Файл завдання (необов\'язково)',
        }


class StudentSubmissionForm(forms.ModelForm):
    class Meta:
        model = StudentSubmission
        fields = ['file', 'comment']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Додаткові коментарі до роботи...'}),
        }
        labels = {
            'file': 'Файл роботи',
            'comment': 'Коментар'
        }


class GradeSubmissionForm(forms.ModelForm):
    class Meta:
        model = StudentSubmission
        fields = ['grade', 'teacher_feedback']
        widgets = {
            'grade': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'}),
            'teacher_feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Введіть відгук до роботи студента...'}),
        }
        labels = {
            'grade': 'Оцінка',
            'teacher_feedback': 'Відгук викладача'
        }
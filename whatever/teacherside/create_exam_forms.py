from django import forms
from .models import Exam

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['title', 'description', 'deadline', 'class_designation', 'timelimit', 'attempt_limit', 'access_code', 'access_status']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'timelimit': forms.TimeInput(attrs={'type': 'time'}),
        }

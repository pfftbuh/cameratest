from django import forms
from .models import Exam
from datetime import timedelta

class ExamForm(forms.ModelForm):
    timelimit = forms.IntegerField(
        min_value=20,
        help_text="Enter the time limit in minutes"
    )

    class Meta:
        model = Exam
        fields = ['title', 'description', 'deadline', 'class_designation',
                  'timelimit', 'attempt_limit', 'access_code', 'access_status']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean_timelimit(self):
        minutes = self.cleaned_data['timelimit']
        return timedelta(minutes=minutes)


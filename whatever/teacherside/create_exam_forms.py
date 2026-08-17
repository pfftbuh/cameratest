from django import forms
from .models import Exam, Question
from homepage.models import CustomUser
from datetime import timedelta

class ExamForm(forms.ModelForm):
    timelimit = forms.IntegerField(
        min_value=20,
        help_text="Enter the time limit in minutes"
    )
    
    class_designation = forms.ChoiceField(
        choices=[],
        required=True,
        help_text="Select a class from existing student designations"
    )

    class Meta:
        model = Exam
        fields = ['title', 'description', 'deadline', 'class_designation',
                  'timelimit', 'attempt_limit', 'access_code', 'access_status']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get unique class designations from students
        class_designations = CustomUser.objects.filter(
            role='student',
            class_designation__isnull=False
        ).exclude(
            class_designation=''
        ).values_list('class_designation', flat=True).distinct().order_by('class_designation')
        
        # Create choices list
        choices = [('', '--- Select a class ---')] + [(cd, cd) for cd in class_designations]
        self.fields['class_designation'].choices = choices
        
        # If no classes exist, add a help message
        if len(class_designations) == 0:
            self.fields['class_designation'].help_text = "⚠️ No student classes found. Please assign class designations to students first."

    def clean_timelimit(self):
        minutes = self.cleaned_data['timelimit']
        return timedelta(minutes=minutes)

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text', 'question_image', 'question_type', 
                  'correct_answer_text', 'correct_answer_image']
        widgets = {
            'question_text': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'question_type': forms.Select(attrs={'id': 'id_question_type', 'class': 'form-control'}),
        }


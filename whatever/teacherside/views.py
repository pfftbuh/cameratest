from django.shortcuts import render
from .create_exam_forms import ExamForm

# Create your views here.
def teacher_home(request):
    return render(request, 'teacherside/teacher_landing_page.html')

def create_exam(request):
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            form.save()
    else:
        form = ExamForm()
    return render(request, 'teacherside/create_exam.html', {'form': form})
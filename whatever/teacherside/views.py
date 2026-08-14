from django.shortcuts import render, redirect
from .create_exam_forms import ExamForm
from django.contrib import messages

# Create your views here.
def teacher_home(request):
    return render(request, 'teacherside/teacher_landing_page.html')

def create_exam(request):
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Exam created successfully.")
            return redirect('create_exam')
        else:
            messages.error(request, "There was an error creating the exam. Please check the form for errors.")
            return render(request, 'teacherside/create_exam.html', {'form': form})
    else:
        form = ExamForm()
    return render(request, 'teacherside/create_exam.html', {'form': form})
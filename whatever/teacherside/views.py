from django.shortcuts import render

# Create your views here.
def teacher_home(request):
    return render(request, 'teacherside/teacher_landing_page.html')

def create_exam(request):
    return render(request, 'teacherside/create_exam.html')
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

# Every student page sits behind a login: an exam session has to be attributable
# to a named student, and the proctoring log is worthless if it is not.
@login_required
def student_home(request):
    # Access role directly on the user
    if not request.user.is_student():
        messages.error(request, 'Access denied: Students only')
        return redirect('landing_page')
    
    return render(request, 'studentside/student_landing_page.html')


@login_required
def test_exam(request):
    return render(request, 'studentside/test_exam.html')

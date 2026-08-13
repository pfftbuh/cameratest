from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Answer, Exam, ExamAttempt, Question


def login_view(request):
    """Barebones login form. Users must already exist (created via /admin)."""
    if request.user.is_authenticated:
        return redirect('exam_list')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('exam_list')
        error = 'Invalid username or password.'

    return render(request, 'exam/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def exam_list(request):
    exams = Exam.objects.all()
    return render(request, 'exam/exam_list.html', {'exams': exams})


@login_required
def take_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    # Reuse an in-progress attempt if one exists, otherwise start fresh.
    attempt, _ = ExamAttempt.objects.get_or_create(
        user=request.user, exam=exam, submitted_at=None,
        defaults={},
    )

    if request.method == 'POST':
        for question in exam.questions.all():
            choice = request.POST.get(f'question_{question.id}')
            if choice:
                Answer.objects.update_or_create(
                    attempt=attempt, question=question,
                    defaults={'selected_choice': choice},
                )

        correct_count = sum(
            1 for answer in attempt.answers.select_related('question')
            if answer.selected_choice == answer.question.correct_choice
        )
        attempt.score = correct_count
        attempt.submitted_at = timezone.now()
        attempt.save()
        return redirect('exam_result', attempt_id=attempt.id)

    return render(request, 'exam/take_exam.html', {'exam': exam})


@login_required
def exam_result(request, attempt_id):
    attempt = get_object_or_404(ExamAttempt, id=attempt_id, user=request.user)
    total_questions = attempt.exam.questions.count()
    return render(request, 'exam/exam_result.html', {
        'attempt': attempt,
        'total_questions': total_questions,
    })

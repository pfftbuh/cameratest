from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from teacherside.models import Exam
import json

# Every student page sits behind a login: an exam session has to be attributable
# to a named student, and the proctoring log is worthless if it is not.
@login_required
def student_home(request):
    # Access role directly on the user
    if not request.user.is_student():
        messages.error(request, 'Access denied: Students only')
        return redirect('landing_page')
    
    # Get exams for the student's class
    student_class = request.user.class_designation
    
    if student_class:
        exams = Exam.objects.filter(class_designation=student_class).order_by('-created_at')
    else:
        exams = []
    
    # Add access information to each exam
    now = timezone.now()
    for exam in exams:
        exam.is_accessible = exam.access_status and exam.deadline > now
        exam.deadline_passed = exam.deadline <= now
    
    return render(request, 'studentside/student_landing_page.html', {
        'exams': exams,
        'student_class': student_class,
    })


@login_required
def exam_details(request):
    """Show exam instructions before starting calibration/proctoring."""
    exam_id = request.GET.get('exam_id')
    
    if not exam_id:
        messages.error(request, 'No exam specified')
        return redirect('student_home')
    
    try:
        exam = Exam.objects.get(exam_id=exam_id)
    except Exam.DoesNotExist:
        messages.error(request, 'Exam not found')
        return redirect('student_home')
    
    # Store exam_id in session for downstream pages
    request.session['current_exam_id'] = exam_id
    
    return render(request, 'studentside/test_exam.html', {
        'exam': exam,
    })


@login_required
def exam_session(request):
    """Display the exam questions for the student to answer."""
    exam_id = request.session.get('current_exam_id')
    
    if not exam_id:
        messages.error(request, 'No exam selected. Please start from the exam details page.')
        return redirect('student_home')
    
    try:
        exam = Exam.objects.get(exam_id=exam_id)
        questions = exam.questions.all().order_by('question_id')
        
        # Ensure choices is properly formatted
        for question in questions:
            if question.choices and isinstance(question.choices, str):
                import json
                question.choices = json.loads(question.choices)
        
        # Track exam start time (only set once per exam attempt)
        session_key = f'exam_{exam_id}_start_time'
        if session_key not in request.session:
            request.session[session_key] = timezone.now().isoformat()
        
        # Calculate remaining time
        start_time = timezone.datetime.fromisoformat(request.session[session_key])
        if timezone.is_naive(start_time):
            start_time = timezone.make_aware(start_time)
        
        elapsed = (timezone.now() - start_time).total_seconds()
        total_seconds = exam.timelimit.total_seconds()
        remaining_seconds = max(0, int(total_seconds - elapsed))
        
        # If time is up, prevent access
        if remaining_seconds <= 0:
            messages.warning(request, 'Time is up for this exam.')
            # Clear the start time since the exam time has expired
            del request.session[session_key]
            return redirect('student_home')
        
        return render(request, 'studentside/exam_session.html', {
            'exam': exam,
            'questions': questions,
            'remaining_seconds': remaining_seconds,  # Pass calculated time to template
        })
    except Exam.DoesNotExist:
        messages.error(request, 'Exam not found')
        return redirect('student_home')


from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from .models import StudentTrackingThresholds


@login_required
@require_http_methods(["POST"])
def save_tracking_thresholds(request):
    """Save calibrated eye tracking thresholds for the logged-in student."""
    try:
        data = json.loads(request.body)
        thresholds = data.get('thresholds')
        
        if not thresholds:
            return JsonResponse({'success': False, 'error': 'No thresholds provided'})
        
        # Validate that user is a student
        if not request.user.is_student():
            return JsonResponse({'success': False, 'error': 'Only students can save thresholds'})
        
        # Create or update thresholds for this student
        obj, created = StudentTrackingThresholds.objects.update_or_create(
            student=request.user,
            defaults={
                'calibration_up': thresholds.get('up', 0.0),
                'calibration_down': thresholds.get('down', 0.0),
                'calibration_center': thresholds.get('center', 0.0),
                'calibration_left': thresholds.get('left', 0.0),
                'calibration_right': thresholds.get('right', 0.0),
                'calibration_v_center': thresholds.get('v_center', 0.0),
                'iris_boxheight_center': thresholds.get('iris_boxheight_center', 0.0),
                'iris_boxheight_up': thresholds.get('iris_boxheight_up', 0.0),
                'iris_boxheight_down': thresholds.get('iris_boxheight_down', 0.0),
            }
        )
        
        action = "created" if created else "updated"
        return JsonResponse({
            'success': True, 
            'message': f'Thresholds {action} successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
        
def submit_exam(request):
    exam_id = request.session.get('current_exam_id')
    # ... save answers ...
    
    # Clear the start time
    session_key = f'exam_{exam_id}_start_time'
    if session_key in request.session:
        del request.session[session_key]
    
    # ... rest of submission logic ...

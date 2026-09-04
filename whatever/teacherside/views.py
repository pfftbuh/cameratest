from django.shortcuts import render, redirect, get_object_or_404
from .create_exam_forms import ExamForm, QuestionForm
from django.contrib import messages
from .models import Exam, Question
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from homepage.models import CustomUser
from django.db.models import Q, Count, Max, Avg, Sum
from django.http import FileResponse, Http404, HttpResponse
from studentside.models import StudentExamAttempt, ProctoringSessionFiles
import os
import time
import mimetypes
import zipfile
from io import BytesIO

# Create your views here.
def teacher_home(request):
    return render(request, 'teacherside/teacher_landing_page.html')

def manage_students(request):
    """View to list and search students with their class designations."""
    search_query = request.GET.get('search', '')
    
    # Get all students
    students = CustomUser.objects.filter(role='student')
    
    # Apply search filter if query exists
    if search_query:
        students = students.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(class_designation__icontains=search_query)
        )
    
    # Order by username
    students = students.order_by('username')
    
    context = {
        'students': students,
        'search_query': search_query,
        'total_count': CustomUser.objects.filter(role='student').count(),
        'filtered_count': students.count()
    }
    
    return render(request, 'teacherside/manage_students.html', context)

def update_student_class(request, user_id):
    """View to update a student's class designation."""
    if request.method == 'POST':
        student = get_object_or_404(CustomUser, id=user_id, role='student')
        class_designation = request.POST.get('class_designation', '').strip()
        
        student.class_designation = class_designation
        student.save()
        
        messages.success(request, f"Class designation updated for {student.username}")
        return redirect('manage_students')
    
    return redirect('manage_students')

def create_exam(request):
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = request.user  # Manually set the creator
            exam.save()
            return redirect('add_questions', exam_id=exam.exam_id)
        else:
            messages.error(request, "There was an error creating the exam. Please check the form for errors.")
            return render(request, 'teacherside/create_exam.html', {'form': form})
    else:
        form = ExamForm()
    return render(request, 'teacherside/create_exam.html', {'form': form})

def exams_list(request):
    exams = Exam.objects.all().order_by('-created_at')
    return render(request, 'teacherside/exams_list.html', {'exams': exams})

def add_questions(request, exam_id):
    exam = Exam.objects.get(exam_id=exam_id)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, request.FILES)
        if form.is_valid():
            question = form.save(commit=False)
            question.exam = exam
            
            # Handle MCQ choices from dynamic form fields
            if question.question_type == 'MCQ':
                choices = []
                choice_num = 1
                correct_choice_num = request.POST.get('correct_choice')
                
                # Collect all choice fields
                while f'choice_text_{choice_num}' in request.POST:
                    choice_text = request.POST.get(f'choice_text_{choice_num}')
                    choice_image = request.FILES.get(f'choice_image_{choice_num}')
                    
                    if choice_text:
                        choice_data = {
                            'text': choice_text,
                            'image': None
                        }
                        
                        # Handle choice image upload to media storage
                        if choice_image:
                            # Create a unique filename to avoid conflicts
                            timestamp = int(time.time() * 1000)
                            ext = os.path.splitext(choice_image.name)[1]
                            filename = f'choice_images/exam_{exam_id}_choice_{choice_num}_{timestamp}{ext}'
                            # Save the file
                            path = default_storage.save(filename, ContentFile(choice_image.read()))
                            choice_data['image'] = path
                        
                        choices.append(choice_data)
                        
                        # Set correct answer text if this choice is marked as correct
                        if correct_choice_num and int(correct_choice_num) == choice_num:
                            question.correct_answer_text = choice_text
                    
                    choice_num += 1
                
                import json
                question.choices = json.dumps(choices)
                
                # Validate that a correct answer was selected
                if not question.correct_answer_text:
                    messages.error(request, "Please select which choice is the correct answer.")
                    return render(request, 'teacherside/add_questions.html', {
                        'form': form,
                        'exam': exam,
                        'questions': Question.objects.filter(exam=exam).order_by('created_at')
                    })
            
            question.save()
            messages.success(request, "Question added successfully!")
            return redirect('add_questions', exam_id=exam_id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = QuestionForm()
    
    # Get existing questions for this exam
    questions = Question.objects.filter(exam=exam).order_by('created_at')
    
    return render(request, 'teacherside/add_questions.html', {
        'form': form,
        'exam': exam,
        'questions': questions
    })

def modify_exam(request, exam_id):
    exam = Exam.objects.get(exam_id=exam_id)
    
    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            messages.success(request, "Exam details updated successfully!")
            return redirect('modify_exam', exam_id=exam_id)
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        # Convert timelimit back to minutes for display
        initial_data = {
            'timelimit': int(exam.timelimit.total_seconds() / 60) if exam.timelimit else 60
        }
        form = ExamForm(instance=exam, initial=initial_data)
    
    questions = Question.objects.filter(exam=exam).order_by('created_at')
    
    # Parse JSON choices for each MCQ question
    import json
    for question in questions:
        if question.question_type == 'MCQ' and question.choices:
            try:
                question.choices = json.loads(question.choices) if isinstance(question.choices, str) else question.choices
            except:
                question.choices = []
    
    return render(request, 'teacherside/modify_exam.html', {
        'exam': exam,
        'form': form,
        'questions': questions
    })

def delete_question(request, question_id):
    if request.method == 'POST':
        question = Question.objects.get(question_id=question_id)
        exam_id = question.exam.exam_id
        question.delete()
        messages.success(request, "Question deleted successfully!")
        return redirect('modify_exam', exam_id=exam_id)
    return redirect('exams_list')


# Proctoring Session File Views

def exam_attempts_list(request, exam_id):
    """List all students who attempted a specific exam"""
    exam = get_object_or_404(Exam, exam_id=exam_id)
    
    # Get all attempts for this exam with related data
    attempts_summary = StudentExamAttempt.objects.filter(exam=exam).values(
        'student__id',
        'student__username', 
        'student__first_name',
        'student__last_name',
        'student__class_designation'
    ).annotate(
        total_attempts=Count('id'),
        best_score=Max('score'),
        avg_score=Avg('score'),
        avg_suspicion=Avg('prediction_confidence'),
        total_violations=Sum('violation_count')
    ).order_by('student__username')

    for summary in attempts_summary:
        summary['avg_suspicion_percent'] = summary['avg_suspicion'] * 100 if summary['avg_suspicion'] is not None else None
    
    context = {
        'exam': exam,
        'attempts_summary': attempts_summary,
    }
    
    return render(request, 'teacherside/exam_attempts_list.html', context)


def student_attempt_detail(request, exam_id, student_id):
    """Show all attempts by a specific student for an exam"""
    exam = get_object_or_404(Exam, exam_id=exam_id)
    student = get_object_or_404(CustomUser, id=student_id, role='student')
    
    # Get all attempts by this student for this exam
    attempts = StudentExamAttempt.objects.filter(
        exam=exam, 
        student=student
    ).order_by('-attempt_number')
    
    # Attach session files to each attempt
    for attempt in attempts:
        if attempt.prediction_status == 'completed':
            label = 'Non-cheating' if attempt.prediction_label == 'non_cheating' else 'Cheating'
            attempt.suspicion_display = (
                f'{label} - {attempt.prediction_confidence * 100:.0f}%'
            )
        else:
            attempt.suspicion_display = (
                attempt.prediction_status or 'pending'
            ).title()
        if attempt.proctoring_session_id:
            try:
                attempt.files = ProctoringSessionFiles.objects.get(
                    session_id=attempt.proctoring_session_id
                )
            except ProctoringSessionFiles.DoesNotExist:
                attempt.files = None
        else:
            attempt.files = None
    
    context = {
        'exam': exam,
        'student': student,
        'attempts': attempts,
    }
    
    return render(request, 'teacherside/student_attempt_detail.html', context)


def download_session_file(request, session_id, file_type, index=None):
    """
    Download a specific file from a proctoring session
    file_type: 'calibration', 'heatmap', 'csv', 'video'
    index: required for 'csv' and 'video' types (0-based)
    """
    try:
        session_files = ProctoringSessionFiles.objects.get(session_id=session_id)
    except ProctoringSessionFiles.DoesNotExist:
        raise Http404("Session files not found")
    
    file_path = None
    filename = None
    
    if file_type == 'calibration':
        file_path = session_files.get_calibration_path()
        filename = 'eye_calibration.json'
    
    elif file_type == 'heatmap':
        file_path = session_files.get_heatmap_path()
        filename = f'heatmap_{session_id}.png'
    
    elif file_type == 'csv':
        if index is None:
            raise Http404("CSV index is required")
        csv_paths = session_files.get_all_csv_paths()
        if not csv_paths or not (0 <= index < len(csv_paths)):
            raise Http404("CSV file not found at specified index")
        file_path = csv_paths[index]
        filename = os.path.basename(file_path) if file_path else None
    
    elif file_type == 'video':
        if index is None:
            raise Http404("Video index is required")
        video_paths = session_files.get_all_video_paths()
        if not video_paths or not (0 <= index < len(video_paths)):
            raise Http404("Video file not found at specified index")
        file_path = video_paths[index]
        filename = os.path.basename(file_path) if file_path else None
    
    else:
        raise Http404("Invalid file type")
    
    if not file_path or not os.path.exists(file_path):
        raise Http404("File not found on server")
    
    # Determine content type
    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        content_type = 'application/octet-stream'
    
    # Open and serve the file
    try:
        file_handle = open(file_path, 'rb')
        response = FileResponse(file_handle, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except IOError:
        raise Http404("Error reading file")


def view_session_file(request, session_id, file_type, index=None):
    """View file in browser (for images, JSON, CSV)"""
    try:
        session_files = ProctoringSessionFiles.objects.get(session_id=session_id)
    except ProctoringSessionFiles.DoesNotExist:
        raise Http404("Session files not found")
    
    file_path = None
    content_type = 'text/plain'
    
    if file_type == 'calibration':
        file_path = session_files.get_calibration_path()
        content_type = 'application/json'
    
    elif file_type == 'heatmap':
        file_path = session_files.get_heatmap_path()
        content_type = 'image/png'
    
    elif file_type == 'csv':
        if index is None:
            raise Http404("CSV index is required")
        csv_paths = session_files.get_all_csv_paths()
        if not csv_paths or not (0 <= index < len(csv_paths)):
            raise Http404("CSV file not found")
        file_path = csv_paths[index]
        content_type = 'text/csv'
    
    else:
        raise Http404("Invalid file type for viewing")
    
    if not file_path or not os.path.exists(file_path):
        raise Http404("File not found on server")
    
    try:
        file_handle = open(file_path, 'rb')
        response = FileResponse(file_handle, content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'
        return response
    except IOError:
        raise Http404("Error reading file")


def download_all_session_files(request, session_id):
    """Create a ZIP file with all session files for download"""
    try:
        session_files = ProctoringSessionFiles.objects.get(session_id=session_id)
    except ProctoringSessionFiles.DoesNotExist:
        raise Http404("Session files not found")
    
    # Create in-memory ZIP file
    zip_buffer = BytesIO()
    file_count = 0
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add calibration JSON
        if session_files.calibration_file:
            path = session_files.get_calibration_path()
            if path and os.path.exists(path):
                zip_file.write(path, os.path.basename(path))
                file_count += 1
        
        # Add heatmap
        if session_files.heatmap_image:
            path = session_files.get_heatmap_path()
            if path and os.path.exists(path):
                zip_file.write(path, os.path.basename(path))
                file_count += 1
        
        # Add all CSVs
        for csv_path in session_files.get_all_csv_paths():
            if csv_path and os.path.exists(csv_path):
                zip_file.write(csv_path, os.path.basename(csv_path))
                file_count += 1
        
        # Add all videos
        for video_path in session_files.get_all_video_paths():
            if video_path and os.path.exists(video_path):
                zip_file.write(video_path, os.path.basename(video_path))
                file_count += 1
    
    if file_count == 0:
        raise Http404("No files found for this session")
    
    # Prepare response
    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="session_{session_id}_files.zip"'
    
    return response
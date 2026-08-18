from django.shortcuts import render, redirect, get_object_or_404
from .create_exam_forms import ExamForm, QuestionForm
from django.contrib import messages
from .models import Exam, Question
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from homepage.models import CustomUser
from studentside.models import StudentExamAttempt
from django.db.models import Q
import os
import time

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
    
    return render(request, 'teacherside/add_questions.html', {
        'form': form,
        'exam': exam,
        'questions': questions
    })

def monitor_exam(request, exam_id):
    """Live proctoring wall for one exam.

    Renders the shell only — every student tile arrives over the monitor
    WebSocket, so the page stays current without polling.
    """
    exam = get_object_or_404(Exam, exam_id=exam_id)

    # Teacher-only. The other views in this module have no access check at all,
    # which is worth fixing separately; this one exposes live webcam thumbnails
    # of the whole cohort, so it cannot wait.
    user = request.user
    if not user.is_authenticated:
        return redirect('login')
    if not (getattr(user, 'is_teacher', lambda: False)() or user.is_staff):
        messages.error(request, 'Access denied: Teachers only')
        return redirect('landing_page')

    attempts = StudentExamAttempt.objects.filter(exam=exam).select_related('student')

    return render(request, 'teacherside/monitor_exam.html', {
        'exam': exam,
        'attempt_count': attempts.count(),
    })

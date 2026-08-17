from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from teacherside.models import Exam, Question
from studentside.models import StudentExamAttempt, StudentAnswer, StudentTrackingThresholds


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'is_staff', 'date_joined']
    list_filter = ['role', 'is_staff', 'is_active']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )
    
@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['exam_id', 'title', 'description', 'deadline', 'class_designation', 'timelimit', 'attempt_limit', 'access_code', 'access_status', 'created_at', 'updated_at']
    list_filter = ['class_designation', 'access_status']
    search_fields = ['title', 'description', 'class_designation']
    ordering = ['-created_at']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_id', 'exam', 'question_text', 'question_type']
    list_filter = ['exam', 'question_type']
    search_fields = ['question_text']
    ordering = ['-question_id']

@admin.register(StudentExamAttempt)
class StudentExamAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam', 'attempt_number', 'score', 'completed_at']
    list_filter = ['exam', 'completed_at']
    search_fields = ['student__username', 'exam__title']
    ordering = ['-completed_at']

@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ['student_exam_attempt', 'question', 'answer_text', 'answer_image']
    list_filter = ['question']
    search_fields = ['student_exam_attempt__student__username', 'question__question_text']
    ordering = ['-student_exam_attempt']

@admin.register(StudentTrackingThresholds)
class StudentTrackingThresholdsAdmin(admin.ModelAdmin):
    list_display = ['student', 'calibration_up', 'calibration_down', 'calibration_center', 'calibration_left', 'calibration_right', 'calibration_v_center', 'iris_boxheight_center', 'iris_boxheight_up', 'iris_boxheight_down', 'calibrated_at']
    search_fields = ['student__username']
    ordering = ['-calibrated_at']



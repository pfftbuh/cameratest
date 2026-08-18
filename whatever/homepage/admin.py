from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from teacherside.models import Exam, Question


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





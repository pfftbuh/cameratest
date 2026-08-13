from django.contrib import admin

from .models import Answer, Exam, ExamAttempt, Question


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title',)
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('exam', 'text', 'correct_choice', 'order')
    list_filter = ('exam',)


@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'exam', 'started_at', 'submitted_at', 'score')
    list_filter = ('exam',)
    readonly_fields = ('started_at',)


admin.site.register(Answer)

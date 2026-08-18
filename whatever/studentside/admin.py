from django.contrib import admin
from .models import StudentExamAttempt, StudentAnswer, StudentTrackingThresholds, ProctoringSessionFiles

# Register your models here.

@admin.register(StudentExamAttempt)
class StudentExamAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'attempt_number', 'score', 'completed_at', 'suspicion_score', 'violation_count')
    list_filter = ('exam', 'completed_at')
    search_fields = ('student__username', 'exam__title')
    readonly_fields = ('proctoring_started_at', 'proctoring_ended_at', 'completed_at')

@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ('student_exam_attempt', 'question', 'answer_text', 'answer_image')
    list_filter = ('question',)
    search_fields = ('student_exam_attempt__student__username', 'question__question_text')

@admin.register(StudentTrackingThresholds)
class StudentTrackingThresholdsAdmin(admin.ModelAdmin):
    list_display = ('student', 'calibration_center', 'calibration_up', 'calibration_down', 'calibration_left', 'calibration_right', 'calibrated_at')
    search_fields = ('student__username',)
    readonly_fields = ('calibrated_at',)

@admin.register(ProctoringSessionFiles)
class ProctoringSessionFilesAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'exam_attempt', 'has_calibration', 'has_heatmap', 'csv_count', 'video_count', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('session_id', 'exam_attempt__student__username')
    readonly_fields = ('session_id', 'session_directory', 'created_at', 'updated_at')
    
    def has_calibration(self, obj):
        return bool(obj.calibration_file)
    has_calibration.boolean = True
    has_calibration.short_description = 'Calibration'
    
    def has_heatmap(self, obj):
        return bool(obj.heatmap_image)
    has_heatmap.boolean = True
    has_heatmap.short_description = 'Heatmap'
    
    def csv_count(self, obj):
        return len(obj.session_log_csvs)
    csv_count.short_description = 'CSVs'
    
    def video_count(self, obj):
        return len(obj.violation_videos)
    video_count.short_description = 'Videos'

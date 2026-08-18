from django.db import models

# Create your models here.

class StudentExamAttempt(models.Model):
    student = models.ForeignKey('homepage.CustomUser', on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    exam = models.ForeignKey('teacherside.Exam', on_delete=models.CASCADE)
    attempt_number = models.PositiveIntegerField()
    score = models.FloatField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Proctoring integration fields
    proctoring_session_id = models.CharField(max_length=100, null=True, blank=True, 
                                              help_text="WebSocket session ID for proctoring")
    proctoring_started_at = models.DateTimeField(null=True, blank=True)
    proctoring_ended_at = models.DateTimeField(null=True, blank=True)
    suspicion_score = models.FloatField(default=0.0, help_text="Cumulative suspicion score")
    violation_count = models.IntegerField(default=0, help_text="Number of flagged violations")

    class Meta:
        unique_together = ('student', 'exam', 'attempt_number')

    def __str__(self):
        return f"{self.student.username} - {self.exam.title} (Attempt {self.attempt_number})"

# Use to store the answers for each question in a student's exam attempt in a JSON format. This allows for flexibility in storing different types of answers (text, image, etc.) depending on the question type.
class StudentAnswer(models.Model):
    student_exam_attempt = models.ForeignKey(StudentExamAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey('teacherside.Question', on_delete=models.CASCADE)
    answer_text = models.TextField(null=True, blank=True)
    answer_image = models.ImageField(upload_to='student_answers/', null=True, blank=True)

    def __str__(self):
        return f"Answer for {self.question} by {self.student_exam_attempt.student.username}"

# Student Gaze Tracking Thresholds
class StudentTrackingThresholds(models.Model):
    student = models.OneToOneField('homepage.CustomUser', on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    
    # Individual calibration threshold fields
    calibration_up = models.FloatField()
    calibration_down = models.FloatField()
    calibration_center = models.FloatField()
    calibration_left = models.FloatField()
    calibration_right = models.FloatField()
    calibration_v_center = models.FloatField()
    iris_boxheight_center = models.FloatField()
    iris_boxheight_up = models.FloatField()
    iris_boxheight_down = models.FloatField()
    
    calibrated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Thresholds for {self.student.username}"
    
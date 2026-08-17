from django.db import models

# Create your models here.

class StudentExamAttempt(models.Model):
    student = models.ForeignKey('homepage.CustomUser', on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    exam = models.ForeignKey('teacherside.Exam', on_delete=models.CASCADE)
    attempt_number = models.PositiveIntegerField()
    score = models.FloatField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

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

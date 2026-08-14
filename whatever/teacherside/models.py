from django.db import models

# Create your models here.
class Exam(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    deadline = models.DateTimeField()
    class_designation = models.CharField(max_length=100)
    timelimit = models.DurationField(help_text="Enter the time limit for the exam (e.g., 1:30:00 for 1 hour 30 minutes).")
    attempt_limit = models.PositiveIntegerField(help_text="Enter the maximum number of attempts allowed for this exam.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
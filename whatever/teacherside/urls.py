from django.urls import path
from . import views

urlpatterns = [
    path('', views.teacher_home, name='teacher_home'),
    path('exams/', views.exams_list, name='exams_list'),
    path('create_exam/', views.create_exam, name='create_exam'),
    path('exam/<int:exam_id>/add_questions/', views.add_questions, name='add_questions'),
    path('exam/<int:exam_id>/modify/', views.modify_exam, name='modify_exam'),
    path('question/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('exam/<int:exam_id>/monitor/', views.monitor_exam, name='monitor_exam'),
    path('students/', views.manage_students, name='manage_students'),
    path('student/<int:user_id>/update-class/', views.update_student_class, name='update_student_class'),
]

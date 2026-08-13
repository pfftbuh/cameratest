from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/<int:exam_id>/take/', views.take_exam, name='take_exam'),
    path('exams/result/<int:attempt_id>/', views.exam_result, name='exam_result'),
]

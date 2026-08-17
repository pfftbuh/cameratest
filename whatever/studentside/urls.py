from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.student_home, name='student_home'),
    path('camera/', include('camera.urls')),
    path('exam_details/', views.exam_details, name='exam_details'),
    path('exam_session/', views.exam_session, name='exam_session'),
    path('save-tracking-thresholds/', views.save_tracking_thresholds, name='save_tracking_thresholds'),
]
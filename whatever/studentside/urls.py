from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.student_home, name='student_home'),
    path('camera/', include('camera.urls')),
    path('test_exam/', views.test_exam, name='test_exam'),
]
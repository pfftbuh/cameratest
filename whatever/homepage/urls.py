from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('studentside/', include('studentside.urls')),
    path('teacherside/', include('teacherside.urls')),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]

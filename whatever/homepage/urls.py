from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('studentside/', include('studentside.urls')),
    path('login/', views.login_view, name='login'),
]
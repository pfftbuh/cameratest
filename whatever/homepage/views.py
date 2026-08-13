from django.shortcuts import render

# Create your views here.
def landing_page(request):
    return render(request, 'homepage/landing_page.html')

def login_view(request):
    return render(request, 'homepage/login.html')
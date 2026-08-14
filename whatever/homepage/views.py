from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import SignUpForm


def landing_page(request):
    return render(request, 'homepage/landing_page.html')


def signup_view(request):
    """Create a student account, then send them to the login page.

    Deliberately not logging the new user straight in: signing in with the
    credentials just created is the step that proves registration worked, and
    it's the flow that gets demonstrated.
    """
    if request.user.is_authenticated:
        return redirect('student_home')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f'Account created for {user.username}. Sign in with your new credentials.'
            )
            return redirect('login')
    else:
        form = SignUpForm()

    return render(request, 'homepage/signup_page.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('student_home')

    # AuthenticationForm does the authenticate() call and rejects inactive
    # accounts, so a wrong password produces a form error rather than a crash.
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        auth_login(request, form.get_user())

        # Honour ?next= so @login_required sends people back where they were,
        # but only for local paths — an open redirect would let someone bounce
        # a student off this login page to an external site.
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url and next_url.startswith('/') and not next_url.startswith('//'):
            return redirect(next_url)
        return redirect('student_home')

    return render(request, 'homepage/login_page.html', {
        'form': form,
        'next': request.GET.get('next', ''),
    })


@require_POST
def logout_view(request):
    auth_logout(request)
    messages.success(request, 'You have been signed out.')
    return redirect(reverse('landing_page'))

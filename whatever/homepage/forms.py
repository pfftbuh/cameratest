from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    """Registration form for students.

    Django's UserCreationForm already handles the username-taken check, the
    password confirmation and the password strength validators from
    AUTH_PASSWORD_VALIDATORS. This adds email as a required field so an account
    can be tied back to a real student.
    """

    email = forms.EmailField(
        required=True,
        help_text='Use your university address.',
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        # Not enforced by Django's User model, but two accounts sharing an email
        # would make a student impossible to identify from an exam log.
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

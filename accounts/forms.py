from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import CustomUser


class BaseUserForm(UserCreationForm):
    """Common fields for both student and teacher registration."""
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")


class StudentRegistrationForm(BaseUserForm):
    """Registration form that forces the role to STUDENT."""
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.STUDENT
        if commit:
            user.save()
        return user


class TeacherRegistrationForm(BaseUserForm):
    """Registration form that forces the role to TEACHER."""
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.TEACHER
        if commit:
            user.save()
        return user


class ProfileForm(UserChangeForm):
    """Allow a logged‑in user to edit their basic profile data."""
    password = None  # Hide the password field

    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email")

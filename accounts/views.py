from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import StudentRegistrationForm, TeacherRegistrationForm, ProfileForm
from .models import CustomUser


def register(request):
    """Handle registration for both students and teachers."""
    # Determine initial selected role based on URL
    if 'teacher' in request.path:
        selected_role = CustomUser.TEACHER
    else:
        selected_role = CustomUser.STUDENT

    if request.method == "POST":
        role = request.POST.get("role", selected_role)
        selected_role = role
        if role == CustomUser.TEACHER:
            teacher_form = TeacherRegistrationForm(request.POST)
            student_form = StudentRegistrationForm()
            active_form = teacher_form
        else:
            student_form = StudentRegistrationForm(request.POST)
            teacher_form = TeacherRegistrationForm()
            active_form = student_form

        if active_form.is_valid():
            user = active_form.save()
            login(request, user)
            messages.success(request, f"Welcome to SmartEdu, {user.username}!")
            return redirect("dashboard")
    else:
        student_form = StudentRegistrationForm()
        teacher_form = TeacherRegistrationForm()

    return render(request, "accounts/register.html", {
        "student_form": student_form,
        "teacher_form": teacher_form,
        "selected_role": selected_role,
    })


@login_required
def profile(request):
    """Allow a logged‑in user to view and edit their profile."""
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/profile.html", {"form": form})


def logout_view(request):
    """Log the user out and redirect to the home page."""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")

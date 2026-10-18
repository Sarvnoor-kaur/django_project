from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Course, Enrollment


def teacher_required(view_func):
    """Decorator ensuring logged-in user has the TEACHER role."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        if not getattr(request.user, 'is_teacher', lambda: False)():
            raise PermissionDenied("Only instructors are permitted to access this resource.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def student_required(view_func):
    """Decorator ensuring logged-in user has the STUDENT role."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        if not getattr(request.user, 'is_student', lambda: False)():
            raise PermissionDenied("Only enrolled students are permitted to access this action.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def check_course_ownership(user, course):
    """Verify that the user is the instructor who created this course."""
    if not (user.is_authenticated and course.teacher_id == user.id):
        raise PermissionDenied("You do not have permission to manage this course.")


def is_student_enrolled(user, course):
    """Check if the student has an active enrollment in the course."""
    if not user.is_authenticated:
        return False
    return Enrollment.objects.filter(student=user, course=course, active=True).exists()


def check_course_access(user, course):
    """Verify user is either the course instructor or an enrolled student."""
    if not user.is_authenticated:
        raise PermissionDenied("Authentication required to access course content.")
    if course.teacher_id == user.id:
        return True
    if is_student_enrolled(user, course):
        return True
    raise PermissionDenied("You must be enrolled in this course to view its lessons.")

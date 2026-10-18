from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    """User model with a role field for Student or Teacher.

    Extends Django's ``AbstractUser`` so we keep the standard authentication
    fields (username, email, password, etc.) and add a ``role`` choice.
    Helper properties ``is_student`` and ``is_teacher`` are provided for
    convenient role checks throughout the codebase.
    """

    STUDENT = 'STUDENT'
    TEACHER = 'TEACHER'

    ROLE_CHOICES = [
        (STUDENT, 'Student'),
        (TEACHER, 'Teacher'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=STUDENT,
        help_text='Designates whether the user is a student or a teacher.',
    )

    def is_student(self) -> bool:
        """Return True if the user is a student."""
        return self.role == self.STUDENT

    def is_teacher(self) -> bool:
        """Return True if the user is a teacher."""
        return self.role == self.TEACHER

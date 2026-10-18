from django.db import models
from django.conf import settings


class Conversation(models.Model):
    """Persistent chat session between a student/teacher and the Demo AI Tutor."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_conversations'
    )
    title = models.CharField(max_length=255, default="New Conversation")
    course = models.ForeignKey(
        'learning.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_conversations'
    )
    lesson = models.ForeignKey(
        'learning.Lesson',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_conversations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title} ({self.created_at.strftime('%Y-%m-%d')})"


class Message(models.Model):
    """An individual user or AI message within a conversation."""
    ROLE_USER = 'user'
    ROLE_ASSISTANT = 'assistant'
    ROLE_CHOICES = [
        (ROLE_USER, 'User'),
        (ROLE_ASSISTANT, 'AI Tutor'),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]

    def __str__(self):
        return f"[{self.role}] {self.content[:40]}..."

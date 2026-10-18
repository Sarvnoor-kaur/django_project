from django.urls import path
from . import views

app_name = 'ai_tutor'

urlpatterns = [
    # Main Chat
    path('', views.tutor_chat, name='tutor_chat_default'),
    path('chat/<int:conversation_id>/', views.tutor_chat, name='tutor_chat'),
    path('chat/<int:conversation_id>/send/', views.send_message, name='send_message'),
    path('new/', views.new_conversation, name='new_conversation'),
    path('delete/<int:conversation_id>/', views.delete_conversation, name='delete_conversation'),
    path('history/', views.conversation_history, name='conversation_history'),

    # Contextual Lesson Actions
    path('lesson/<int:lesson_id>/<str:action>/', views.lesson_ai_action, name='lesson_ai_action'),

    # Analytics
    path('analytics/student/', views.student_analytics_view, name='student_analytics'),
    path('analytics/teacher/', views.teacher_analytics_view, name='teacher_analytics'),

    # Teacher AI Drafting Studio
    path('teacher/drafting/', views.teacher_draft_tool, name='teacher_drafting'),
]

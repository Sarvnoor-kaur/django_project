"""
Views for SmartEdu Demo AI Tutor, Analytics, and Teacher AI Drafting.

Implements strict object-level authorization, persistent chat history,
context-aware lesson querying, and server-side validated input processing.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest
from django.db import transaction

from learning.models import Course, Lesson, Enrollment
from .models import Conversation, Message
from .knowledge_base import KNOWLEDGE_BASE
from .services.ai_engine import process_user_query, generate_fallback_response
from .services.lesson_assistant import (
    verify_user_lesson_access,
    summarize_lesson_content,
    extract_lesson_key_points,
    generate_lesson_revision_questions,
    recommend_next_lesson_steps,
)
from .services.teacher_assistant import (
    verify_teacher_lesson_ownership,
    verify_teacher_course_ownership,
    draft_lesson_summary,
    draft_lesson_key_points,
    draft_revision_questions,
    draft_topic_outline,
)
from .services.analytics import get_student_analytics, get_teacher_analytics
from .services.recommendations import get_student_recommendations


# ==============================================================================
# AI TUTOR CHAT VIEWS
# ==============================================================================

@login_required
def tutor_chat(request, conversation_id=None):
    """
    Main interactive chat interface for the Demo AI Tutor.
    Loads active conversation, sidebar history, and contextual suggestions.
    """
    user_conversations = Conversation.objects.filter(user=request.user).order_by('-updated_at')
    active_conversation = None

    if conversation_id:
        active_conversation = get_object_or_404(Conversation, id=conversation_id)
        if active_conversation.user_id != request.user.id and not request.user.is_superuser:
            raise PermissionDenied("You do not have permission to view this conversation.")
    else:
        # Check if user has an existing conversation or create a default one
        active_conversation = user_conversations.first()
        if not active_conversation:
            active_conversation = Conversation.objects.create(
                user=request.user,
                title="Learning with AI Tutor"
            )
            # Welcome message from AI Tutor
            Message.objects.create(
                conversation=active_conversation,
                role=Message.ROLE_ASSISTANT,
                content=(
                    "👋 **Hello! I'm your SmartEdu Demo AI Tutor.**\n\n"
                    "I am a specialized, local rule-based educational assistant designed to help you master "
                    "computer science concepts, summarize lessons, practice active recall with revision questions, "
                    "and guide your study roadmap.\n\n"
                    "💡 *Try asking me about Python, Django, Databases, Operating Systems, or Networking!*"
                )
            )

    # Optional query parameters to initialize context
    lesson_id = request.GET.get('lesson_id')
    context_lesson = None
    if lesson_id:
        try:
            lesson = get_object_or_404(Lesson, id=lesson_id)
            verify_user_lesson_access(request.user, lesson)
            context_lesson = lesson
            if active_conversation and not active_conversation.lesson:
                active_conversation.lesson = lesson
                active_conversation.course = lesson.course
                active_conversation.save(update_fields=['lesson', 'course', 'updated_at'])
        except (ValueError, PermissionDenied):
            pass

    chat_messages = active_conversation.messages.all().order_by('created_at') if active_conversation else []

    topics_summary = [
        {'key': k, 'name': v['topic_name'], 'category': v['category']}
        for k, v in KNOWLEDGE_BASE.items()
    ]

    return render(request, 'ai_tutor/chat.html', {
        'conversation': active_conversation,
        'user_conversations': user_conversations[:15],
        'chat_messages': chat_messages,
        'context_lesson': context_lesson or (active_conversation.lesson if active_conversation else None),
        'context_course': active_conversation.course if active_conversation else None,
        'topics_summary': topics_summary,
    })


@login_required
@require_POST
def send_message(request, conversation_id):
    """
    Handle message submission from the user, run deterministic intent matching,
    and append assistant response to the conversation.
    """
    conversation = get_object_or_404(Conversation, id=conversation_id)
    if conversation.user_id != request.user.id and not request.user.is_superuser:
        raise PermissionDenied("You cannot post to this conversation.")

    user_text = request.POST.get('message', '').strip()

    if not user_text:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': "Message cannot be empty."}, status=400)
        messages.warning(request, "Please enter a question or topic.")
        return redirect('ai_tutor:tutor_chat', conversation_id=conversation.id)

    if len(user_text) > 1000:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': "Message exceeds 1,000 characters limit."}, status=400)
        messages.error(request, "Message too long. Please limit your query to 1,000 characters.")
        return redirect('ai_tutor:tutor_chat', conversation_id=conversation.id)

    with transaction.atomic():
        # Save user message
        user_msg = Message.objects.create(
            conversation=conversation,
            role=Message.ROLE_USER,
            content=user_text
        )

        # Update conversation title if first user message
        if conversation.messages.filter(role=Message.ROLE_USER).count() == 1:
            clean_title = (user_text[:35] + "...") if len(user_text) > 35 else user_text
            conversation.title = clean_title
            conversation.save(update_fields=['title', 'updated_at'])

        # Process via AI engine
        engine_result = process_user_query(user_text)
        assistant_content = engine_result.get('response', generate_fallback_response(user_text))

        # Save assistant message
        assistant_msg = Message.objects.create(
            conversation=conversation,
            role=Message.ROLE_ASSISTANT,
            content=assistant_content
        )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'user_message': {
                'id': user_msg.id,
                'content': user_msg.content,
                'created_at': user_msg.created_at.strftime('%H:%M'),
            },
            'assistant_message': {
                'id': assistant_msg.id,
                'content': assistant_msg.content,
                'created_at': assistant_msg.created_at.strftime('%H:%M'),
            }
        })

    return redirect('ai_tutor:tutor_chat', conversation_id=conversation.id)


@login_required
def new_conversation(request):
    """Start a new clean chat session."""
    lesson_id = request.GET.get('lesson_id')
    course_id = request.GET.get('course_id')
    lesson = None
    course = None

    if lesson_id:
        lesson = get_object_or_404(Lesson, id=lesson_id)
        verify_user_lesson_access(request.user, lesson)
        course = lesson.course
    elif course_id:
        course = get_object_or_404(Course, id=course_id)

    title = f"Study: {lesson.title}" if lesson else (f"Course: {course.title}" if course else "New Conversation")

    conv = Conversation.objects.create(
        user=request.user,
        title=title,
        course=course,
        lesson=lesson
    )

    # Initial contextual welcome
    welcome = (
        f"📘 **Ready to study {lesson.title}!**\n\n"
        "You can ask me to **summarize this lesson**, **extract key points**, "
        "or **generate practice revision questions**."
        if lesson else
        "👋 **New session started!** What computer science concept or lesson would you like to explore?"
    )
    Message.objects.create(conversation=conv, role=Message.ROLE_ASSISTANT, content=welcome)

    return redirect('ai_tutor:tutor_chat', conversation_id=conv.id)


@login_required
@require_POST
def delete_conversation(request, conversation_id):
    """Delete a conversation owned by the authenticated user."""
    conv = get_object_or_404(Conversation, id=conversation_id)
    if conv.user_id != request.user.id and not request.user.is_superuser:
        raise PermissionDenied("You cannot delete this conversation.")

    conv.delete()
    messages.success(request, "Conversation deleted successfully.")
    return redirect('ai_tutor:tutor_chat_default')


@login_required
def conversation_history(request):
    """View and search complete history of user's AI conversations."""
    conversations = Conversation.objects.filter(user=request.user).select_related('course', 'lesson').order_by('-updated_at')

    query = request.GET.get('q', '').strip()
    if query:
        conversations = conversations.filter(title__icontains=query)

    return render(request, 'ai_tutor/history.html', {
        'conversations': conversations,
        'query': query,
    })


# ==============================================================================
# LESSON DIRECT AI ACTIONS (from Lesson viewer)
# ==============================================================================

@login_required
def lesson_ai_action(request, lesson_id, action):
    """
    Trigger a direct AI action from the lesson detail page (summarize, key_points,
    revision_questions, next_steps) and open in the tutor chat.
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    verify_user_lesson_access(request.user, lesson)

    # Find or create a conversation for this lesson
    conv = Conversation.objects.filter(user=request.user, lesson=lesson).order_by('-updated_at').first()
    if not conv:
        conv = Conversation.objects.create(
            user=request.user,
            title=f"Study: {lesson.title}",
            course=lesson.course,
            lesson=lesson
        )

    # Execute action
    if action == 'summarize':
        user_prompt = f"Summarize lesson: {lesson.title}"
        res = summarize_lesson_content(lesson)
        ai_reply = res.get('summary')
    elif action == 'key_points':
        user_prompt = f"Extract key points for: {lesson.title}"
        res = extract_lesson_key_points(lesson)
        ai_reply = res.get('key_points')
    elif action == 'questions':
        user_prompt = f"Generate revision questions for: {lesson.title}"
        res = generate_lesson_revision_questions(lesson)
        ai_reply = res.get('questions')
    elif action == 'next_steps':
        user_prompt = f"What should I study next after {lesson.title}?"
        res = recommend_next_lesson_steps(request.user, lesson)
        ai_reply = res.get('recommendation')
    else:
        user_prompt = f"Explain lesson: {lesson.title}"
        res = summarize_lesson_content(lesson)
        ai_reply = res.get('summary')

    # Atomic creation of user prompt and AI response
    with transaction.atomic():
        Message.objects.create(conversation=conv, role=Message.ROLE_USER, content=user_prompt)
        Message.objects.create(conversation=conv, role=Message.ROLE_ASSISTANT, content=ai_reply)

    return redirect('ai_tutor:tutor_chat', conversation_id=conv.id)


# ==============================================================================
# ANALYTICS VIEWS
# ==============================================================================

@login_required
def student_analytics_view(request):
    """Comprehensive learning analytics and personalized study roadmap for students."""
    if not request.user.is_student() and not request.user.is_superuser:
        messages.info(request, "Instructors can view course analytics on the Teacher Analytics page.")
        return redirect('ai_tutor:teacher_analytics')

    analytics_data = get_student_analytics(request.user)
    recommendations = get_student_recommendations(request.user)

    return render(request, 'ai_tutor/student_analytics.html', {
        'analytics': analytics_data,
        'recommendations': recommendations,
    })


@login_required
def teacher_analytics_view(request):
    """Instructor-level curriculum engagement and assessment analytics."""
    if not request.user.is_teacher() and not request.user.is_superuser:
        raise PermissionDenied("Only instructors can view Teacher Analytics.")

    analytics_data = get_teacher_analytics(request.user)

    return render(request, 'ai_tutor/teacher_analytics.html', {
        'analytics': analytics_data,
    })


# ==============================================================================
# TEACHER AI DRAFTING TOOLS
# ==============================================================================

@login_required
def teacher_draft_tool(request):
    """
    Teacher-facing AI drafting workspace.
    Enables instructors to draft lesson summaries, key points, practice questions,
    and lesson outlines strictly for courses and lessons they own.
    """
    if not request.user.is_teacher() and not request.user.is_superuser:
        raise PermissionDenied("Only instructors can access the AI Drafting Studio.")

    teacher_courses = Course.objects.filter(teacher=request.user).prefetch_related('lessons')
    selected_lesson_id = request.GET.get('lesson_id')
    selected_course_id = request.GET.get('course_id')

    selected_lesson = None
    if selected_lesson_id:
        try:
            lesson = get_object_or_404(Lesson, id=selected_lesson_id)
            verify_teacher_lesson_ownership(request.user, lesson)
            selected_lesson = lesson
        except PermissionDenied:
            messages.error(request, "You can only draft content for your own lessons.")

    generated_draft = ""
    draft_title = ""
    error_msg = ""

    if request.method == 'POST':
        action = request.POST.get('action')
        post_lesson_id = request.POST.get('lesson_id')
        topic_query = request.POST.get('topic_query', '').strip()

        if action in ['summary', 'key_points', 'questions'] and post_lesson_id:
            lesson = get_object_or_404(Lesson, id=post_lesson_id)
            verify_teacher_lesson_ownership(request.user, lesson)
            selected_lesson = lesson

            if action == 'summary':
                res = draft_lesson_summary(request.user, lesson)
            elif action == 'key_points':
                res = draft_lesson_key_points(request.user, lesson)
            else:
                res = draft_revision_questions(request.user, lesson)

            if res.get('success'):
                generated_draft = res['draft']
                draft_title = res.get('title', 'AI-Assisted Draft')
            else:
                error_msg = res.get('error', 'Could not generate draft.')

        elif action == 'outline' and topic_query:
            res = draft_topic_outline(request.user, topic_query)
            if res.get('success'):
                generated_draft = res['draft']
                draft_title = res.get('title', 'Curriculum Outline Draft')

    return render(request, 'ai_tutor/teacher_drafting.html', {
        'teacher_courses': teacher_courses,
        'selected_lesson': selected_lesson,
        'generated_draft': generated_draft,
        'draft_title': draft_title,
        'error_msg': error_msg,
        'supported_topics': list(KNOWLEDGE_BASE.values()),
    })

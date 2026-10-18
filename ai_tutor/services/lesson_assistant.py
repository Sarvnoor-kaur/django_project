"""
Context-Aware Lesson Assistance Service for SmartEdu Demo AI Tutor.

Securely inspects authenticated lesson content to provide explanations, summaries,
key points, revision questions, and next-step recommendations based strictly on
authorized course materials.
"""

import re
from typing import Dict, Any, List
from django.core.exceptions import PermissionDenied
from learning.models import Lesson, Course, Enrollment


def verify_user_lesson_access(user, lesson: Lesson) -> None:
    """
    Ensure the user is authorized to view this lesson.
    - Course instructor is always authorized.
    - Students must have an active enrollment in the course.
    - Superusers/staff are authorized.
    Raises PermissionDenied if unauthorized.
    """
    if not user.is_authenticated:
        raise PermissionDenied("You must be logged in to access this lesson.")

    if user.is_superuser or user.is_staff:
        return

    # Check course teacher
    if lesson.course.teacher_id == user.id:
        return

    # Check student enrollment
    is_enrolled = Enrollment.objects.filter(
        student=user,
        course=lesson.course,
        active=True
    ).exists()

    if not is_enrolled:
        raise PermissionDenied("You must be enrolled in this course to access this lesson with AI Tutor.")


def summarize_lesson_content(lesson: Lesson) -> Dict[str, Any]:
    """
    Generate a deterministic, grounded summary of the lesson's actual text content.
    Flags when text is insufficient or empty.
    """
    content = (getattr(lesson, 'lesson_content', None) or getattr(lesson, 'content', None) or "").strip()
    words = content.split()

    if len(words) < 25:
        return {
            'success': False,
            'summary': (
                f"⚠️ **Lesson content is brief** ({len(words)} words).\n\n"
                f"The instructor has not added sufficient detailed material to '{lesson.title}' "
                "to generate a multi-point summary. Review the lesson overview directly or consult uploaded course resources."
            ),
            'word_count': len(words)
        }

    # Extract sentences deterministically
    sentences = [s.strip() for s in re.split(r'[.!?]+', content) if len(s.strip().split()) >= 4]

    # Select leading thesis sentence and key points
    intro = sentences[0] if sentences else content[:120]
    key_sentences = sentences[1:5] if len(sentences) > 1 else [content[:150]]

    bullets = "\n".join([f"• {s}." for s in key_sentences])

    result_text = (
        f"### 📝 Grounded Lesson Summary: {lesson.title}\n"
        f"**Course:** {lesson.course.title} | **Order:** Lesson #{lesson.ordering}\n\n"
        f"**Overview:** {intro}.\n\n"
        f"#### Core Concepts Covered in this Lesson:\n"
        f"{bullets}\n\n"
        f"*(Generated from authentic lesson text — {len(words)} words analyzed)*"
    )

    return {
        'success': True,
        'summary': result_text,
        'word_count': len(words)
    }


def extract_lesson_key_points(lesson: Lesson) -> Dict[str, Any]:
    """Extract key takeaways from the lesson's headings and substantive sentences."""
    content = (getattr(lesson, 'lesson_content', None) or getattr(lesson, 'content', None) or "").strip()
    words = content.split()

    if len(words) < 20:
        return {
            'success': False,
            'key_points': (
                f"⚠️ **Insufficient content** in lesson '{lesson.title}'.\n\n"
                "Key points require at least 20 words of text. Please read the lesson text directly."
            )
        }

    # Split into paragraphs and sentences
    paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
    points = []

    for p in paragraphs:
        # Check if paragraph has heading-like or strong intro
        sents = [s.strip() for s in re.split(r'[.!?]+', p) if len(s.strip().split()) >= 4]
        if sents:
            points.append(sents[0])
        if len(points) >= 5:
            break

    if not points:
        points = [content[:120]]

    points_formatted = "\n".join([f"**{i+1}.** {pt}." for i, pt in enumerate(points)])

    return {
        'success': True,
        'key_points': (
            f"### 🎯 Key Points: {lesson.title}\n"
            f"**Course:** {lesson.course.title}\n\n"
            f"{points_formatted}\n\n"
            f"💡 **Self-Check:** Can you explain each of these points in your own words?"
        )
    }


def generate_lesson_revision_questions(lesson: Lesson) -> Dict[str, Any]:
    """Generate transparent, curriculum-grounded revision questions based on lesson content."""
    content = (getattr(lesson, 'lesson_content', None) or getattr(lesson, 'content', None) or "").strip()
    words = content.split()

    if len(words) < 20:
        return {
            'success': False,
            'questions': (
                f"⚠️ **Not enough lesson text** to formulate revision questions for '{lesson.title}'.\n\n"
                "Take a look at the course assessments or ask the tutor about the general topic instead!"
            )
        }

    sentences = [s.strip() for s in re.split(r'[.!?]+', content) if len(s.strip().split()) >= 5]
    
    questions = []
    # Q1 based on title
    questions.append(
        f"**Question 1:** What is the primary objective of '{lesson.title}' and how does it fit into {lesson.course.title}?\n"
        f"> *Review the introduction section of this lesson for the conceptual definition.*"
    )

    if len(sentences) >= 2:
        questions.append(
            f"**Question 2:** Explain the significance of this concept discussed in the lesson: \"{sentences[0][:90]}...\"\n"
            f"> *Analyze why this principle is emphasized in the curriculum.*"
        )
    if len(sentences) >= 4:
        questions.append(
            f"**Question 3:** How does the following point apply in practical scenarios: \"{sentences[2][:90]}...\"?\n"
            f"> *Connect this lesson point with practical software implementation.*"
        )
    
    # Check if lesson has video/resource
    if lesson.video_url:
        questions.append(
            f"**Question 4:** How does the video demonstration complement the written text in this lesson?\n"
            f"> *Review the multimedia walkthrough to verify real-world behavior.*"
        )

    return {
        'success': True,
        'questions': (
            f"### ✍️ Lesson Revision Questions: {lesson.title}\n"
            f"Test your understanding of the material taught in this specific lesson:\n\n"
            + "\n\n".join(questions) + "\n\n"
            f"*(Transparent Rule-Based Quiz Assistant — based strictly on lesson contents)*"
        )
    }


def recommend_next_lesson_steps(user, lesson: Lesson) -> Dict[str, Any]:
    """Recommend next logical study step after current lesson."""
    course = lesson.course
    # Find next lesson in order
    next_lesson = course.lessons.filter(ordering__gt=lesson.ordering).order_by('ordering').first()
    
    # Check for course quizzes
    quizzes = course.quizzes.filter(is_published=True).order_by('created_at')[:2]

    msg = [f"### 🧭 Next Study Steps for {course.title}\n"]

    if next_lesson:
        msg.append(
            f"**Recommended Next Lesson:**\n"
            f"👉 **Lesson {next_lesson.ordering}: {next_lesson.title}**\n"
            f"Continue sequentially to maintain learning momentum.\n"
        )
    else:
        msg.append(
            f"🎉 **You have reached the final lesson of {course.title}!**\n"
            f"Review the full curriculum or test your mastery with the course quizzes below.\n"
        )

    if quizzes.exists():
        msg.append("**Assess Your Understanding:**")
        for q in quizzes:
            msg.append(f"• 📝 **{q.title}** ({q.questions.count()} questions, {q.passing_percentage}% pass mark)")

    return {
        'success': True,
        'recommendation': "\n".join(msg),
        'next_lesson_id': next_lesson.id if next_lesson else None
    }

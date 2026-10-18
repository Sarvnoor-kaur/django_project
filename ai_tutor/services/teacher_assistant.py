"""
Teacher-Facing AI Drafting Service for SmartEdu.

Assists instructors in drafting lesson summaries, key points, practice questions,
and structured curriculum outlines. Scoped strictly to courses owned by the instructor.
Returns editable drafts labeled clearly for teacher review before saving.
"""

import re
from typing import Dict, Any, List
from django.core.exceptions import PermissionDenied
from learning.models import Lesson, Course
from ai_tutor.knowledge_base import KNOWLEDGE_BASE


def verify_teacher_lesson_ownership(teacher, lesson: Lesson) -> None:
    """Ensure the user is a teacher and owns the course associated with this lesson."""
    if not teacher.is_authenticated or not teacher.is_teacher():
        raise PermissionDenied("Only instructors can access teacher AI drafting tools.")
    if lesson.course.teacher_id != teacher.id and not teacher.is_superuser:
        raise PermissionDenied("You can only draft content for lessons you created.")


def verify_teacher_course_ownership(teacher, course: Course) -> None:
    """Ensure the user is a teacher and owns the course."""
    if not teacher.is_authenticated or not teacher.is_teacher():
        raise PermissionDenied("Only instructors can access teacher AI drafting tools.")
    if course.teacher_id != teacher.id and not teacher.is_superuser:
        raise PermissionDenied("You can only draft content for courses you created.")


def draft_lesson_summary(teacher, lesson: Lesson) -> Dict[str, Any]:
    """Generate an editable draft summary for an instructor's lesson."""
    verify_teacher_lesson_ownership(teacher, lesson)
    content = (getattr(lesson, 'lesson_content', None) or getattr(lesson, 'content', None) or "").strip()
    words = content.split()

    if len(words) < 20:
        return {
            'success': False,
            'draft': "",
            'error': "Lesson content contains fewer than 20 words. Please add more lesson details first."
        }

    sentences = [s.strip() for s in re.split(r'[.!?]+', content) if len(s.strip().split()) >= 4]
    main_sentence = sentences[0] if sentences else content[:100]
    supporting = sentences[1:4] if len(sentences) > 1 else []

    draft = (
        f"### Summary of {lesson.title}\n\n"
        f"**Core Objective:** {main_sentence}.\n\n"
        f"**Main Takeaways:**\n"
        + ("\n".join([f"- {s}." for s in supporting]) if supporting else "- Key lesson concepts.") + "\n\n"
        f"---\n*AI-assisted draft — review, edit, and adjust tone before publishing.*"
    )

    return {
        'success': True,
        'draft': draft,
        'title': f"Draft Summary for {lesson.title}"
    }


def draft_lesson_key_points(teacher, lesson: Lesson) -> Dict[str, Any]:
    """Generate editable key points for an instructor's lesson."""
    verify_teacher_lesson_ownership(teacher, lesson)
    content = (getattr(lesson, 'lesson_content', None) or getattr(lesson, 'content', None) or "").strip()
    words = content.split()

    if len(words) < 20:
        return {
            'success': False,
            'draft': "",
            'error': "Lesson content contains fewer than 20 words. Add more lesson body text first."
        }

    paragraphs = [p.strip() for p in content.split('\n') if len(p.strip().split()) >= 4]
    points = []
    for p in paragraphs[:5]:
        sents = [s.strip() for s in re.split(r'[.!?]+', p) if len(s.strip().split()) >= 4]
        if sents:
            points.append(sents[0])

    if not points:
        points = [s.strip() for s in re.split(r'[.!?]+', content) if len(s.strip().split()) >= 4][:4]

    draft = (
        f"### Key Learning Points: {lesson.title}\n\n"
        + "\n".join([f"{i+1}. **{pt}.**" for i, pt in enumerate(points)]) + "\n\n"
        f"---\n*AI-assisted draft — review and customize before adding to lesson notes.*"
    )

    return {
        'success': True,
        'draft': draft,
        'title': f"Draft Key Points for {lesson.title}"
    }


def draft_revision_questions(teacher, lesson: Lesson) -> Dict[str, Any]:
    """Generate editable revision questions with model answers for the instructor."""
    verify_teacher_lesson_ownership(teacher, lesson)
    content = (getattr(lesson, 'lesson_content', None) or getattr(lesson, 'content', None) or "").strip()
    words = content.split()

    if len(words) < 20:
        return {
            'success': False,
            'draft': "",
            'error': "Lesson has insufficient content to formulate revision questions."
        }

    sentences = [s.strip() for s in re.split(r'[.!?]+', content) if len(s.strip().split()) >= 4]

    draft = (
        f"### Suggested Revision Questions for '{lesson.title}'\n\n"
        f"**Question 1 (Recall):** What is the core definition and purpose of {lesson.title}?\n"
        f"*Model Answer:* Students should identify the primary concept introduced in the opening section.\n\n"
        + (f"**Question 2 (Application):** Based on: \"{sentences[0][:100]}...\", how does a student implement this in practice?\n"
           f"*Model Answer:* Provide a concrete coding example or configuration snippet.\n\n" if sentences else "") +
        f"**Question 3 (Synthesis):** How does this lesson connect with earlier topics in {lesson.course.title}?\n"
        f"*Model Answer:* Students should connect this lesson's concepts to the broader course curriculum.\n\n"
        f"---\n*AI-assisted draft — review, modify, or convert into quiz questions.*"
    )

    return {
        'success': True,
        'draft': draft,
        'title': f"Draft Questions for {lesson.title}"
    }


def draft_topic_outline(teacher, topic_query: str) -> Dict[str, Any]:
    """Generate a structured lesson outline for a supported curriculum topic."""
    if not teacher.is_authenticated or not teacher.is_teacher():
        raise PermissionDenied("Only instructors can generate lesson outlines.")

    # Match against local knowledge base
    query_norm = topic_query.lower().strip()
    matched_data = None
    for k, data in KNOWLEDGE_BASE.items():
        if data['topic_name'].lower() in query_norm or any(kw in query_norm for kw in data['keywords']):
            matched_data = data
            break

    if not matched_data:
        # Fallback to general modular structure
        draft = (
            f"### Proposed Lesson Outline: {topic_query.title()}\n\n"
            f"**Module 1: Introduction & Fundamentals**\n"
            f"- High-level conceptual overview and real-world motivation\n"
            f"- Key terminology and architectural definitions\n\n"
            f"**Module 2: Practical Implementation**\n"
            f"- Step-by-step code demonstration or diagram walkthrough\n"
            f"- Common pitfalls and best practice patterns\n\n"
            f"**Module 3: Hands-On Exercise & Assessment**\n"
            f"- Interactive lab exercise or problem set\n"
            f"- Formative multiple-choice review quiz\n\n"
            f"---\n*AI-assisted draft — customize for your specific course level.*"
        )
    else:
        pts = "\n".join([f"- {pt}" for pt in matched_data['key_points']])
        draft = (
            f"### Proposed Curriculum Outline: {matched_data['topic_name']}\n"
            f"**Domain:** {matched_data['category']}\n\n"
            f"**Module 1: Conceptual Foundation**\n"
            f"- {matched_data['explanation'][:180]}...\n\n"
            f"**Module 2: Core Subject Principles**\n"
            f"{pts}\n\n"
            f"**Module 3: Review & Knowledge Checks**\n"
            f"- Formative quiz on {matched_data['topic_name']}\n"
            f"- Student coding exercise or architectural review\n\n"
            f"---\n*AI-assisted draft grounded in SmartEdu Knowledge Base — review before creating lessons.*"
        )

    return {
        'success': True,
        'draft': draft,
        'title': f"Outline for {topic_query}"
    }

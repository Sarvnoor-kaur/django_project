"""
Personalized Educational Recommendation Service for SmartEdu.

Generates transparent, rule-based recommendations for students based on real
enrollment records, lesson progress, quiz attempts, and category preferences.
Contains clean fallbacks for new accounts and strictly respects course access.
"""

from typing import List, Dict, Any
from django.db.models import Avg, Q
from learning.models import Course, Lesson, Enrollment, LessonProgress, QuizAttempt, Quiz


def get_student_recommendations(student) -> List[Dict[str, Any]]:
    """
    Generate prioritized, personalized recommendations for a student.
    Returns a list of dicts with:
      - title
      - reason
      - url_name / url_kwargs
      - badge (e.g. 'Next Lesson', 'Quiz Revision', 'Continue Course', 'Explore')
      - icon (e.g. 'book', 'arrow-right', 'alert-circle', 'compass')
    """
    recommendations: List[Dict[str, Any]] = []

    if not student.is_authenticated or not student.is_student():
        return recommendations

    # 1. Fetch active enrollments with preloaded courses
    enrollments = Enrollment.objects.filter(
        student=student,
        active=True
    ).select_related('course', 'course__teacher').prefetch_related('course__lessons')

    enrolled_course_ids = [enr.course_id for enr in enrollments]
    enrolled_categories = set(enr.course.category for enr in enrollments if enr.course.category)

    # Completed lesson IDs
    completed_lesson_ids = set(
        LessonProgress.objects.filter(
            student=student,
            is_completed=True
        ).values_list('lesson_id', flat=True)
    )

    # --------------------------------------------------------------------------
    # RULE 1: Next Incomplete Lesson in Enrolled Courses (Top Priority)
    # --------------------------------------------------------------------------
    for enr in enrollments:
        course = enr.course
        lessons = course.lessons.all().order_by('ordering')
        for lesson in lessons:
            if lesson.id not in completed_lesson_ids:
                recommendations.append({
                    'title': f"Lesson {lesson.ordering}: {lesson.title}",
                    'subtitle': course.title,
                    'reason': f"Continue your next incomplete lesson in {course.title}.",
                    'badge': 'Next Lesson',
                    'badge_color': 'indigo',
                    'action_url': f"/learning/courses/{course.slug}/lessons/{lesson.slug}/",
                    'action_label': 'Start Lesson',
                    'icon': 'play-circle',
                })
                break  # Only one next lesson per course

    # --------------------------------------------------------------------------
    # RULE 2: Quiz Revision after Low Score (< 50%) or Failed Attempt
    # --------------------------------------------------------------------------
    recent_low_attempts = QuizAttempt.objects.filter(
        student=student,
        percentage__lt=50.0
    ).select_related('quiz', 'quiz__course').order_by('-submitted_at')[:3]

    for attempt in recent_low_attempts:
        quiz = attempt.quiz
        course = quiz.course
        recommendations.append({
            'title': f"Review Quiz: {quiz.title}",
            'subtitle': course.title,
            'reason': f"Review this topic after scoring {attempt.percentage:.0f}% on your recent attempt.",
            'badge': 'Quiz Revision',
            'badge_color': 'amber',
            'action_url': f"/learning/quizzes/{quiz.id}/take/",
            'action_label': 'Retake Quiz',
            'icon': 'rotate-ccw',
        })

    # --------------------------------------------------------------------------
    # RULE 3: Finish Course Started but Incomplete
    # --------------------------------------------------------------------------
    for enr in enrollments:
        course = enr.course
        total_lessons = course.lessons.count()
        if total_lessons > 0:
            course_completed = len([lid for lid in completed_lesson_ids if course.lessons.filter(id=lid).exists()])
            if 0 < course_completed < total_lessons:
                pct = round((course_completed / total_lessons) * 100)
                # Check if not already added in Rule 1
                if not any(r['subtitle'] == course.title and r['badge'] == 'In Progress' for r in recommendations):
                    recommendations.append({
                        'title': f"{course.title} ({pct}% Complete)",
                        'subtitle': f"{course_completed} of {total_lessons} lessons completed",
                        'reason': f"Finish the course you recently started to earn full certification.",
                        'badge': 'In Progress',
                        'badge_color': 'emerald',
                        'action_url': f"/learning/courses/{course.slug}/",
                        'action_label': 'Resume Course',
                        'icon': 'trending-up',
                    })

    # --------------------------------------------------------------------------
    # RULE 4: Recommend Published Courses Matching Student's Subject Interests
    # --------------------------------------------------------------------------
    if enrolled_categories:
        recommended_courses = Course.objects.filter(
            status=Course.STATUS_PUBLISHED,
            category__in=enrolled_categories
        ).exclude(id__in=enrolled_course_ids).select_related('teacher')[:2]

        for c in recommended_courses:
            recommendations.append({
                'title': c.title,
                'subtitle': f"Category: {c.get_category_display()} • Instructor: {c.teacher.get_full_name() or c.teacher.username}",
                'reason': f"Explore a new course in {c.get_category_display()} based on your current studies.",
                'badge': 'Explore',
                'badge_color': 'purple',
                'action_url': f"/learning/courses/{c.slug}/",
                'action_label': 'View Course',
                'icon': 'compass',
            })

    # --------------------------------------------------------------------------
    # RULE 5: Fallback for New Students with No/Low Records
    # --------------------------------------------------------------------------
    if len(recommendations) < 2:
        popular_courses = Course.objects.filter(
            status=Course.STATUS_PUBLISHED
        ).exclude(id__in=enrolled_course_ids).order_by('-created_at')[:3]

        for c in popular_courses:
            recommendations.append({
                'title': c.title,
                'subtitle': f"{c.get_category_display()} • {c.get_difficulty_level_display()}",
                'reason': "Recommended starting course from our featured catalog.",
                'badge': 'Featured',
                'badge_color': 'blue',
                'action_url': f"/learning/courses/{c.slug}/",
                'action_label': 'Explore Catalog',
                'icon': 'award',
            })

    # Deduplicate and limit to top 5 recommendations
    seen_titles = set()
    final_recs = []
    for r in recommendations:
        if r['title'] not in seen_titles:
            seen_titles.add(r['title'])
            final_recs.append(r)
        if len(final_recs) >= 5:
            break

    return final_recs

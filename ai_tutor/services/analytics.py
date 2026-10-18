"""
Comprehensive Educational Analytics Service for SmartEdu.

Calculates real, database-backed learning analytics for students and instructors.
Includes strict ownership scoping, zero hardcoded numbers, and clean empty states.
"""

from typing import Dict, Any, List
from django.db.models import Count, Avg, Q, Max
from learning.models import Course, Lesson, Enrollment, LessonProgress, Quiz, QuizAttempt


def get_student_analytics(student) -> Dict[str, Any]:
    """Calculate personalized learning analytics for an authenticated student."""
    if not student.is_authenticated or not student.is_student():
        return {}

    # Active enrollments
    enrollments = Enrollment.objects.filter(
        student=student,
        active=True
    ).select_related('course', 'course__teacher').prefetch_related('course__lessons')

    total_enrolled_courses = enrollments.count()
    enrolled_course_ids = [enr.course_id for enr in enrollments]

    # Completed lessons
    completed_progresses = LessonProgress.objects.filter(
        student=student,
        is_completed=True
    ).select_related('lesson', 'lesson__course')

    total_completed_lessons = completed_progresses.count()

    # Per-course breakdown
    courses_breakdown: List[Dict[str, Any]] = []
    total_lessons_all_enrolled = 0

    for enr in enrollments:
        c = enr.course
        course_lessons = list(c.lessons.all())
        lesson_count = len(course_lessons)
        total_lessons_all_enrolled += lesson_count

        completed_in_course = completed_progresses.filter(lesson__course=c).count()
        progress_pct = round((completed_in_course / lesson_count * 100)) if lesson_count > 0 else 0

        # Quiz attempts for this course
        course_attempts = QuizAttempt.objects.filter(
            student=student,
            quiz__course=c,
            submitted_at__isnull=False
        )
        course_avg_score = course_attempts.aggregate(Avg('percentage'))['percentage__avg'] or 0.0

        courses_breakdown.append({
            'course': c,
            'total_lessons': lesson_count,
            'completed_lessons': completed_in_course,
            'progress_pct': progress_pct,
            'avg_score': round(course_avg_score, 1),
            'attempts_count': course_attempts.count(),
            'is_finished': progress_pct >= 100 and lesson_count > 0,
        })

    overall_progress = round((total_completed_lessons / total_lessons_all_enrolled * 100)) if total_lessons_all_enrolled > 0 else 0

    # Quiz stats
    all_attempts = QuizAttempt.objects.filter(
        student=student,
        submitted_at__isnull=False
    ).select_related('quiz', 'quiz__course').order_by('-submitted_at')

    total_quiz_attempts = all_attempts.count()
    passed_attempts = all_attempts.filter(percentage__gte=50.0).count()
    failed_attempts = total_quiz_attempts - passed_attempts
    overall_avg_score = all_attempts.aggregate(Avg('percentage'))['percentage__avg'] or 0.0

    recent_attempts = list(all_attempts[:8])

    return {
        'total_enrolled_courses': total_enrolled_courses,
        'total_completed_lessons': total_completed_lessons,
        'total_lessons_all_enrolled': total_lessons_all_enrolled,
        'overall_progress': overall_progress,
        'courses_breakdown': courses_breakdown,
        'total_quiz_attempts': total_quiz_attempts,
        'passed_attempts': passed_attempts,
        'failed_attempts': failed_attempts,
        'overall_avg_score': round(overall_avg_score, 1),
        'recent_attempts': recent_attempts,
        'has_data': total_enrolled_courses > 0 or total_quiz_attempts > 0,
    }


def get_teacher_analytics(teacher) -> Dict[str, Any]:
    """Calculate instruction and student engagement analytics scoped to the logged-in teacher."""
    if not teacher.is_authenticated or not teacher.is_teacher():
        return {}

    # Teacher's owned courses
    courses = Course.objects.filter(
        teacher=teacher
    ).prefetch_related('lessons', 'quizzes', 'enrollments')

    total_courses = courses.count()
    published_courses = courses.filter(status=Course.STATUS_PUBLISHED).count()
    draft_courses = total_courses - published_courses

    total_lessons = Lesson.objects.filter(course__teacher=teacher).count()
    total_quizzes = Quiz.objects.filter(course__teacher=teacher).count()

    total_enrollments = Enrollment.objects.filter(
        course__teacher=teacher,
        active=True
    ).count()

    # All attempts on this teacher's quizzes
    teacher_attempts = QuizAttempt.objects.filter(
        quiz__course__teacher=teacher,
        submitted_at__isnull=False
    ).select_related('student', 'quiz', 'quiz__course')

    total_attempts_count = teacher_attempts.count()
    avg_quiz_score = teacher_attempts.aggregate(Avg('percentage'))['percentage__avg'] or 0.0

    # Course-by-course breakdown
    course_data: List[Dict[str, Any]] = []
    for c in courses:
        c_lessons_count = c.lessons.count()
        c_enrollment_count = c.enrollments.filter(active=True).count()
        c_quizzes_count = c.quizzes.count()
        
        c_attempts = QuizAttempt.objects.filter(
            quiz__course=c,
            submitted_at__isnull=False
        )
        c_attempts_count = c_attempts.count()
        c_avg_score = c_attempts.aggregate(Avg('percentage'))['percentage__avg'] or 0.0

        course_data.append({
            'course': c,
            'lessons_count': c_lessons_count,
            'quizzes_count': c_quizzes_count,
            'enrolled_students': c_enrollment_count,
            'quiz_attempts': c_attempts_count,
            'avg_score': round(c_avg_score, 1),
        })

    recent_submissions = teacher_attempts.order_by('-submitted_at')[:10]

    return {
        'total_courses': total_courses,
        'published_courses': published_courses,
        'draft_courses': draft_courses,
        'total_lessons': total_lessons,
        'total_quizzes': total_quizzes,
        'total_enrollments': total_enrollments,
        'total_attempts_count': total_attempts_count,
        'avg_quiz_score': round(avg_quiz_score, 1),
        'course_data': course_data,
        'recent_submissions': recent_submissions,
        'has_data': total_courses > 0,
    }

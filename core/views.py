from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden

from accounts.models import CustomUser


def home(request):
    """Public landing page."""
    return render(request, 'core/home.html')


@login_required
def dashboard(request):
    """Redirect to role‑specific dashboard after login."""
    if request.user.is_student():
        return redirect('student_dashboard')
    if request.user.is_teacher():
        return redirect('teacher_dashboard')
    # Fallback – treat as student
    return redirect('student_dashboard')


@login_required
def student_dashboard(request):
    """Student dashboard with real database metrics, course progress, and quiz history."""
    if not request.user.is_student():
        return HttpResponseForbidden('Students only')

    from learning.models import Enrollment, LessonProgress, QuizAttempt, Quiz
    from django.db.models import Avg

    enrollments = Enrollment.objects.filter(
        student=request.user,
        active=True
    ).select_related('course', 'course__teacher').prefetch_related('course__lessons')

    enrolled_courses_data = []
    total_completed_lessons = LessonProgress.objects.filter(
        student=request.user,
        is_completed=True
    ).count()

    total_lessons_enrolled = 0
    enrolled_course_ids = []

    for enr in enrollments:
        c = enr.course
        enrolled_course_ids.append(c.id)
        lessons = list(c.lessons.all().order_by('ordering'))
        total_course_lessons = len(lessons)
        total_lessons_enrolled += total_course_lessons

        completed_ids = set(
            LessonProgress.objects.filter(
                student=request.user,
                lesson__course=c,
                is_completed=True
            ).values_list('lesson_id', flat=True)
        )
        completed_count = len(completed_ids)
        percent = round((completed_count / total_course_lessons * 100)) if total_course_lessons > 0 else 0

        next_lesson = None
        for l in lessons:
            if l.id not in completed_ids:
                next_lesson = l
                break
        if not next_lesson and lessons:
            next_lesson = lessons[0]

        enrolled_courses_data.append({
            'course': c,
            'percent': percent,
            'completed_count': completed_count,
            'total_lessons': total_course_lessons,
            'next_lesson': next_lesson,
        })

    overall_progress = round((total_completed_lessons / total_lessons_enrolled * 100)) if total_lessons_enrolled > 0 else 0

    recent_attempts = QuizAttempt.objects.filter(
        student=request.user
    ).select_related('quiz', 'quiz__course').order_by('-submitted_at')[:5]

    avg_quiz_score = QuizAttempt.objects.filter(
        student=request.user,
        submitted_at__isnull=False
    ).aggregate(Avg('percentage'))['percentage__avg'] or 0.0

    available_quizzes = Quiz.objects.filter(
        course_id__in=enrolled_course_ids,
        is_published=True
    ).select_related('course')[:4]

    return render(request, 'core/student_dashboard.html', {
        'total_courses': enrollments.count(),
        'total_completed_lessons': total_completed_lessons,
        'overall_progress': overall_progress,
        'avg_quiz_score': round(avg_quiz_score, 1),
        'enrolled_courses': enrolled_courses_data,
        'recent_attempts': recent_attempts,
        'available_quizzes': available_quizzes,
    })


@login_required
def teacher_dashboard(request):
    """Teacher dashboard scoped strictly to courses created by the logged-in teacher."""
    if not request.user.is_teacher():
        return HttpResponseForbidden('Teachers only')

    from learning.models import Course, Enrollment, Lesson, Quiz, QuizAttempt
    from django.db.models import Count, Avg, Q

    courses = Course.objects.filter(
        teacher=request.user
    ).annotate(
        lesson_count=Count('lessons', distinct=True),
        enrolled_count=Count('enrollments', filter=Q(enrollments__active=True), distinct=True)
    ).order_by('-created_at')

    total_courses = courses.count()
    published_courses = courses.filter(status=Course.STATUS_PUBLISHED).count()
    draft_courses = total_courses - published_courses

    total_enrollments = Enrollment.objects.filter(
        course__teacher=request.user,
        active=True
    ).count()

    total_lessons = Lesson.objects.filter(course__teacher=request.user).count()
    total_quizzes = Quiz.objects.filter(course__teacher=request.user).count()

    recent_attempts = QuizAttempt.objects.filter(
        quiz__course__teacher=request.user,
        submitted_at__isnull=False
    ).select_related('student', 'quiz', 'quiz__course').order_by('-submitted_at')[:5]

    return render(request, 'core/teacher_dashboard.html', {
        'courses': courses,
        'total_courses': total_courses,
        'published_courses': published_courses,
        'draft_courses': draft_courses,
        'total_enrollments': total_enrollments,
        'total_lessons': total_lessons,
        'total_quizzes': total_quizzes,
        'recent_attempts': recent_attempts,
    })


def about(request):
    """Static about page."""
    return render(request, 'core/about.html')


def handler403(request, exception=None):
    """Custom 403 forbidden page."""
    response = render(request, 'core/403.html')
    response.status_code = 403
    return response


def handler404(request, exception=None):
    """Custom 404 not‑found page."""
    response = render(request, 'core/404.html')
    response.status_code = 404
    return response

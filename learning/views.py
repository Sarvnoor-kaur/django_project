import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q, Count, Avg, Max
from django.http import HttpResponse, FileResponse, Http404, HttpResponseForbidden
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    Course, Lesson, Resource, Enrollment, LessonProgress,
    Quiz, Question, Choice, QuizAttempt, AttemptAnswer
)
from .forms import (
    CourseForm, LessonForm, ResourceForm, QuizForm, QuestionForm, ChoiceFormSet
)
from .permissions import (
    teacher_required, student_required, check_course_ownership,
    is_student_enrolled, check_course_access
)


# ==============================================================================
# COURSE DISCOVERY & BROWSING (Students & Public)
# ==============================================================================

def course_list(request):
    """Public course catalog with search, category/difficulty filters, and sorting."""
    courses = Course.objects.filter(status=Course.STATUS_PUBLISHED).select_related('teacher')
    
    # Search
    query = request.GET.get('q', '').strip()
    if query:
        courses = courses.filter(
            Q(title__icontains=query) |
            Q(short_description__icontains=query) |
            Q(description__icontains=query)
        )
    
    # Filter by Category
    category = request.GET.get('category', '').strip()
    if category:
        courses = courses.filter(category=category)
        
    # Filter by Difficulty
    difficulty = request.GET.get('difficulty', '').strip()
    if difficulty:
        courses = courses.filter(difficulty_level=difficulty)
        
    # Sorting
    sort = request.GET.get('sort', 'newest')
    if sort == 'title':
        courses = courses.order_by('title')
    elif sort == 'oldest':
        courses = courses.order_by('created_at')
    else:
        courses = courses.order_by('-created_at')

    # Annotate lesson counts
    courses = courses.annotate(
        lesson_count=Count('lessons', distinct=True),
        enrolled_count=Count('enrollments', filter=Q(enrollments__active=True), distinct=True)
    )

    # Pagination (9 per page)
    paginator = Paginator(courses, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Enrolled course IDs for logged-in students
    enrolled_course_ids = set()
    if request.user.is_authenticated and getattr(request.user, 'is_student', lambda: False)():
        enrolled_course_ids = set(
            Enrollment.objects.filter(student=request.user, active=True).values_list('course_id', flat=True)
        )

    return render(request, 'learning/course_list.html', {
        'page_obj': page_obj,
        'categories': [c[0] for c in Course.CATEGORY_CHOICES],
        'difficulty_choices': Course.DIFFICULTY_CHOICES,
        'selected_category': category,
        'selected_difficulty': difficulty,
        'selected_sort': sort,
        'search_query': query,
        'enrolled_course_ids': enrolled_course_ids,
    })


def course_detail(request, slug):
    """Detailed course overview page displaying curriculum, instructor, and enrollment."""
    course = get_object_or_404(
        Course.objects.select_related('teacher').prefetch_related('lessons', 'quizzes', 'resources'),
        slug=slug
    )
    
    # If course is draft, only creator teacher may view it
    if not course.is_published():
        if not (request.user.is_authenticated and course.teacher_id == request.user.id):
            raise Http404("This course is currently not published.")

    enrolled = False
    progress_percentage = 0
    completed_lesson_ids = set()
    
    if request.user.is_authenticated and getattr(request.user, 'is_student', lambda: False)():
        enrolled = is_student_enrolled(request.user, course)
        if enrolled:
            total_lessons = course.lessons.count()
            completed_lesson_ids = set(
                LessonProgress.objects.filter(
                    student=request.user,
                    lesson__course=course,
                    is_completed=True
                ).values_list('lesson_id', flat=True)
            )
            if total_lessons > 0:
                progress_percentage = round((len(completed_lesson_ids) / total_lessons) * 100)

    lessons = course.lessons.all().order_by('ordering', 'created_at')
    resources = course.resources.all()
    quizzes = course.quizzes.filter(is_published=True) if not (request.user.is_authenticated and course.teacher_id == request.user.id) else course.quizzes.all()

    return render(request, 'learning/course_detail.html', {
        'course': course,
        'lessons': lessons,
        'resources': resources,
        'quizzes': quizzes,
        'enrolled': enrolled,
        'progress_percentage': progress_percentage,
        'completed_lesson_ids': completed_lesson_ids,
        'is_teacher_owner': request.user.is_authenticated and course.teacher_id == request.user.id,
    })


@student_required
def my_courses(request):
    """Student's enrolled courses page with progress and resume shortcuts."""
    enrollments = Enrollment.objects.filter(
        student=request.user,
        active=True
    ).select_related('course', 'course__teacher').prefetch_related('course__lessons')

    course_data = []
    for enr in enrollments:
        c = enr.course
        lessons = list(c.lessons.all().order_by('ordering'))
        total_lessons = len(lessons)
        
        completed_ids = set(
            LessonProgress.objects.filter(
                student=request.user,
                lesson__course=c,
                is_completed=True
            ).values_list('lesson_id', flat=True)
        )
        completed_count = len(completed_ids)
        percent = round((completed_count / total_lessons * 100)) if total_lessons > 0 else 0
        
        # Determine next lesson to continue
        next_lesson = None
        for l in lessons:
            if l.id not in completed_ids:
                next_lesson = l
                break
        if not next_lesson and lessons:
            next_lesson = lessons[0]

        course_data.append({
            'course': c,
            'enrolled_at': enr.enrolled_at,
            'total_lessons': total_lessons,
            'completed_count': completed_count,
            'percent': percent,
            'next_lesson': next_lesson,
        })

    return render(request, 'learning/my_courses.html', {
        'course_data': course_data,
    })


# ==============================================================================
# TEACHER COURSE MANAGEMENT
# ==============================================================================

@teacher_required
def teacher_course_list(request):
    """List of all courses created by the logged-in instructor."""
    courses = Course.objects.filter(
        teacher=request.user
    ).annotate(
        lesson_count=Count('lessons', distinct=True),
        enrolled_count=Count('enrollments', filter=Q(enrollments__active=True), distinct=True),
        quiz_count=Count('quizzes', distinct=True)
    ).order_by('-created_at')

    return render(request, 'learning/teacher_course_list.html', {
        'courses': courses,
    })


@teacher_required
def course_create(request):
    """Teacher action to create a new course."""
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            messages.success(request, f"Course '{course.title}' created successfully! Now you can add lessons.")
            return redirect('learning:course_detail', slug=course.slug)
    else:
        form = CourseForm()

    return render(request, 'learning/course_form.html', {
        'form': form,
        'is_edit': False,
    })


@teacher_required
def course_edit(request, slug):
    """Teacher action to modify an existing course."""
    course = get_object_or_404(Course, slug=slug)
    check_course_ownership(request.user, course)

    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Course details updated successfully.")
            return redirect('learning:course_detail', slug=course.slug)
    else:
        form = CourseForm(instance=course)

    return render(request, 'learning/course_form.html', {
        'form': form,
        'course': course,
        'is_edit': True,
    })


@teacher_required
@require_POST
def course_toggle_status(request, slug):
    """Teacher action to quickly publish or unpublish a course."""
    course = get_object_or_404(Course, slug=slug)
    check_course_ownership(request.user, course)

    if course.status == Course.STATUS_PUBLISHED:
        course.status = Course.STATUS_DRAFT
        messages.info(request, f"Course '{course.title}' is now saved as Draft.")
    else:
        course.status = Course.STATUS_PUBLISHED
        messages.success(request, f"Course '{course.title}' is now Published to students!")
    course.save()
    return redirect(request.META.get('HTTP_REFERER') or 'learning:teacher_course_list')


@teacher_required
def course_delete(request, slug):
    """Teacher action to delete a course after explicit confirmation."""
    course = get_object_or_404(Course, slug=slug)
    check_course_ownership(request.user, course)

    if request.method == 'POST':
        title = course.title
        course.delete()
        messages.success(request, f"Course '{title}' has been deleted.")
        return redirect('learning:teacher_course_list')

    return render(request, 'learning/course_confirm_delete.html', {
        'course': course,
    })


# ==============================================================================
# LESSON MANAGEMENT & VIEWING
# ==============================================================================

def lesson_detail(request, course_slug, lesson_slug):
    """Protected lesson view requiring active enrollment or course ownership."""
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, course=course, slug=lesson_slug)
    
    # Access check: enrolled student or teacher owner
    check_course_access(request.user, course)

    # Get ordered lessons for navigation
    lessons = list(course.lessons.all().order_by('ordering', 'created_at'))
    current_index = -1
    for idx, l in enumerate(lessons):
        if l.id == lesson.id:
            current_index = idx
            break

    prev_lesson = lessons[current_index - 1] if current_index > 0 else None
    next_lesson = lessons[current_index + 1] if current_index < len(lessons) - 1 else None

    # Track progress for student
    is_completed = False
    if getattr(request.user, 'is_student', lambda: False)():
        progress, _ = LessonProgress.objects.get_or_create(student=request.user, lesson=lesson)
        is_completed = progress.is_completed

    # Resources related to this lesson or course
    resources = Resource.objects.filter(Q(lesson=lesson) | Q(course=course, lesson__isnull=True))

    return render(request, 'learning/lesson_detail.html', {
        'course': course,
        'lesson': lesson,
        'lessons': lessons,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
        'is_completed': is_completed,
        'resources': resources,
        'is_teacher_owner': course.teacher_id == request.user.id,
    })


@teacher_required
def lesson_create(request, course_slug):
    """Add a new lesson to an instructor's course."""
    course = get_object_or_404(Course, slug=course_slug)
    check_course_ownership(request.user, course)

    max_order = course.lessons.aggregate(m=Max('ordering'))['m'] or 0
    next_order = max_order + 1

    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            messages.success(request, f"Lesson '{lesson.title}' created.")
            return redirect('learning:lesson_detail', course_slug=course.slug, lesson_slug=lesson.slug)
    else:
        form = LessonForm(initial={'ordering': next_order})

    return render(request, 'learning/lesson_form.html', {
        'form': form,
        'course': course,
        'is_edit': False,
    })


@teacher_required
def lesson_edit(request, course_slug, lesson_slug):
    """Edit lesson content or sequence position."""
    course = get_object_or_404(Course, slug=course_slug)
    check_course_ownership(request.user, course)
    lesson = get_object_or_404(Lesson, course=course, slug=lesson_slug)

    if request.method == 'POST':
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, f"Lesson '{lesson.title}' updated.")
            return redirect('learning:lesson_detail', course_slug=course.slug, lesson_slug=lesson.slug)
    else:
        form = LessonForm(instance=lesson)

    return render(request, 'learning/lesson_form.html', {
        'form': form,
        'course': course,
        'lesson': lesson,
        'is_edit': True,
    })


@teacher_required
def lesson_delete(request, course_slug, lesson_slug):
    """Delete a lesson with confirmation."""
    course = get_object_or_404(Course, slug=course_slug)
    check_course_ownership(request.user, course)
    lesson = get_object_or_404(Lesson, course=course, slug=lesson_slug)

    if request.method == 'POST':
        title = lesson.title
        lesson.delete()
        messages.success(request, f"Lesson '{title}' deleted.")
        return redirect('learning:course_detail', slug=course.slug)

    return render(request, 'learning/lesson_confirm_delete.html', {
        'course': course,
        'lesson': lesson,
    })


# ==============================================================================
# RESOURCE MANAGEMENT & SECURE DOWNLOADS
# ==============================================================================

def resource_list(request, course_slug):
    """Display course materials and resources."""
    course = get_object_or_404(Course, slug=course_slug)
    check_course_access(request.user, course)

    resources = course.resources.select_related('lesson').order_by('-created_at')

    return render(request, 'learning/resource_list.html', {
        'course': course,
        'resources': resources,
        'is_teacher_owner': course.teacher_id == request.user.id,
    })


@teacher_required
def resource_create(request, course_slug):
    """Upload a resource for a course or specific lesson."""
    course = get_object_or_404(Course, slug=course_slug)
    check_course_ownership(request.user, course)

    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES, course=course)
        if form.is_valid():
            res = form.save(commit=False)
            res.course = course
            res.uploaded_by = request.user
            res.save()
            messages.success(request, f"Resource '{res.title}' uploaded successfully.")
            return redirect('learning:resource_list', course_slug=course.slug)
    else:
        form = ResourceForm(course=course)

    return render(request, 'learning/resource_form.html', {
        'form': form,
        'course': course,
    })


@teacher_required
@require_POST
def resource_delete(request, course_slug, resource_id):
    """Delete an uploaded resource."""
    course = get_object_or_404(Course, slug=course_slug)
    check_course_ownership(request.user, course)
    res = get_object_or_404(Resource, id=resource_id, course=course)
    
    title = res.title
    res.delete()
    messages.success(request, f"Resource '{title}' deleted.")
    return redirect('learning:resource_list', course_slug=course.slug)


@login_required
def download_resource(request, resource_id):
    """Permission-checked streaming download for private course resources."""
    res = get_object_or_404(Resource.objects.select_related('course'), id=resource_id)
    
    # Must be enrolled student or course owner
    check_course_access(request.user, res.course)

    if not res.file:
        if res.external_url:
            return redirect(res.external_url)
        raise Http404("Resource file is not available.")

    file_path = res.file.path
    if not os.path.exists(file_path):
        raise Http404("File not found on storage server.")

    filename = os.path.basename(file_path)
    response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
    return response


# ==============================================================================
# ENROLLMENT & PROGRESS TRACKING
# ==============================================================================

@student_required
@require_POST
def enroll_course(request, slug):
    """Enroll a student into a published course."""
    course = get_object_or_404(Course, slug=slug)

    if not course.is_published():
        messages.error(request, "Enrollment is unavailable for unpublished courses.")
        return redirect('learning:course_detail', slug=slug)

    with transaction.atomic():
        enrollment, created = Enrollment.objects.get_or_create(
            student=request.user,
            course=course,
            defaults={'active': True}
        )
        if not created and not enrollment.active:
            enrollment.active = True
            enrollment.save()
            messages.success(request, f"You have re-enrolled in '{course.title}'!")
        elif created:
            messages.success(request, f"Congratulations! You are now enrolled in '{course.title}'.")
        else:
            messages.info(request, "You are already enrolled in this course.")

    return redirect('learning:course_detail', slug=slug)


@student_required
@require_POST
def unenroll_course(request, slug):
    """Unenroll student from a course while preserving learning records."""
    course = get_object_or_404(Course, slug=slug)
    enrollment = Enrollment.objects.filter(student=request.user, course=course, active=True).first()

    if enrollment:
        enrollment.active = False
        enrollment.save()
        messages.info(request, f"You have unenrolled from '{course.title}'. Your completion records have been preserved.")
    else:
        messages.warning(request, "You are not enrolled in this course.")

    return redirect('learning:my_courses')


@student_required
@require_POST
def toggle_lesson_progress(request, lesson_id):
    """Toggle lesson completion state for an enrolled student."""
    lesson = get_object_or_404(Lesson.objects.select_related('course'), id=lesson_id)

    if not is_student_enrolled(request.user, lesson.course):
        raise PermissionDenied("You must be enrolled in the course to record lesson completion.")

    progress, _ = LessonProgress.objects.get_or_create(student=request.user, lesson=lesson)
    progress.is_completed = not progress.is_completed
    progress.completed_at = timezone.now() if progress.is_completed else None
    progress.save()

    status_msg = "marked as completed 🎉" if progress.is_completed else "marked as incomplete"
    messages.success(request, f"Lesson '{lesson.title}' {status_msg}.")

    return redirect('learning:lesson_detail', course_slug=lesson.course.slug, lesson_slug=lesson.slug)


# ==============================================================================
# QUIZ & ASSESSMENT SYSTEM
# ==============================================================================

def quiz_list(request, course_slug):
    """List quizzes for a course."""
    course = get_object_or_404(Course, slug=course_slug)
    check_course_access(request.user, course)

    if course.teacher_id == request.user.id:
        quizzes = course.quizzes.all().annotate(question_count=Count('questions'))
    else:
        quizzes = course.quizzes.filter(is_published=True).annotate(question_count=Count('questions'))

    # Load attempt info for students
    attempts_by_quiz = {}
    if getattr(request.user, 'is_student', lambda: False)():
        user_attempts = QuizAttempt.objects.filter(student=request.user, quiz__in=quizzes).order_by('-started_at')
        for att in user_attempts:
            if att.quiz_id not in attempts_by_quiz:
                attempts_by_quiz[att.quiz_id] = att

    return render(request, 'learning/quiz_list.html', {
        'course': course,
        'quizzes': quizzes,
        'attempts_by_quiz': attempts_by_quiz,
        'is_teacher_owner': course.teacher_id == request.user.id,
    })


def quiz_detail(request, quiz_id):
    """Quiz overview page displaying rules, passing score, and previous attempts."""
    quiz = get_object_or_404(Quiz.objects.select_related('course'), id=quiz_id)
    check_course_access(request.user, quiz.course)

    if not quiz.is_published and quiz.course.teacher_id != request.user.id:
        raise Http404("This quiz is currently unavailable.")

    attempts = []
    if request.user.is_authenticated:
        attempts = QuizAttempt.objects.filter(quiz=quiz, student=request.user).order_by('-started_at')

    questions = quiz.questions.all().prefetch_related('choices') if quiz.course.teacher_id == request.user.id else None

    return render(request, 'learning/quiz_detail.html', {
        'quiz': quiz,
        'course': quiz.course,
        'attempts': attempts,
        'questions': questions,
        'is_teacher_owner': quiz.course.teacher_id == request.user.id,
    })


@teacher_required
def quiz_create(request, course_slug):
    """Create a new assessment quiz for an instructor's course."""
    course = get_object_or_404(Course, slug=course_slug)
    check_course_ownership(request.user, course)

    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.course = course
            quiz.created_by = request.user
            quiz.save()
            messages.success(request, f"Quiz '{quiz.title}' created! Now add multiple-choice questions.")
            return redirect('learning:quiz_detail', quiz_id=quiz.id)
    else:
        form = QuizForm()

    return render(request, 'learning/quiz_form.html', {
        'form': form,
        'course': course,
        'is_edit': False,
    })


@teacher_required
def quiz_edit(request, quiz_id):
    """Edit assessment quiz parameters."""
    quiz = get_object_or_404(Quiz.objects.select_related('course'), id=quiz_id)
    check_course_ownership(request.user, quiz.course)

    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, f"Quiz '{quiz.title}' updated.")
            return redirect('learning:quiz_detail', quiz_id=quiz.id)
    else:
        form = QuizForm(instance=quiz)

    return render(request, 'learning/quiz_form.html', {
        'form': form,
        'course': quiz.course,
        'quiz': quiz,
        'is_edit': True,
    })


@teacher_required
def quiz_delete(request, quiz_id):
    """Delete a quiz."""
    quiz = get_object_or_404(Quiz.objects.select_related('course'), id=quiz_id)
    check_course_ownership(request.user, quiz.course)

    if request.method == 'POST':
        course_slug = quiz.course.slug
        quiz.delete()
        messages.success(request, "Quiz deleted successfully.")
        return redirect('learning:quiz_list', course_slug=course_slug)

    return render(request, 'learning/quiz_confirm_delete.html', {
        'quiz': quiz,
    })


@teacher_required
def question_create(request, quiz_id):
    """Add a question and its choices to a quiz."""
    quiz = get_object_or_404(Quiz.objects.select_related('course'), id=quiz_id)
    check_course_ownership(request.user, quiz.course)

    next_order = quiz.questions.count() + 1

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        formset = ChoiceFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                question = form.save(commit=False)
                question.quiz = quiz
                question.save()
                formset.instance = question
                formset.save()
            messages.success(request, "Question and choices saved.")
            return redirect('learning:quiz_detail', quiz_id=quiz.id)
    else:
        form = QuestionForm(initial={'ordering': next_order})
        formset = ChoiceFormSet()

    return render(request, 'learning/question_form.html', {
        'quiz': quiz,
        'form': form,
        'formset': formset,
        'is_edit': False,
    })


@teacher_required
def question_edit(request, question_id):
    """Edit question text, explanation, and choices."""
    question = get_object_or_404(Question.objects.select_related('quiz__course'), id=question_id)
    check_course_ownership(request.user, question.quiz.course)

    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        formset = ChoiceFormSet(request.POST, instance=question)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
            messages.success(request, "Question updated successfully.")
            return redirect('learning:quiz_detail', quiz_id=question.quiz_id)
    else:
        form = QuestionForm(instance=question)
        formset = ChoiceFormSet(instance=question)

    return render(request, 'learning/question_form.html', {
        'quiz': question.quiz,
        'question': question,
        'form': form,
        'formset': formset,
        'is_edit': True,
    })


@teacher_required
@require_POST
def question_delete(request, question_id):
    """Delete a question."""
    question = get_object_or_404(Question.objects.select_related('quiz__course'), id=question_id)
    check_course_ownership(request.user, question.quiz.course)

    quiz_id = question.quiz_id
    question.delete()
    messages.success(request, "Question deleted.")
    return redirect('learning:quiz_detail', quiz_id=quiz_id)


@student_required
def quiz_take(request, quiz_id):
    """Student taking the quiz. Correct choices are NEVER included in HTML."""
    quiz = get_object_or_404(Quiz.objects.select_related('course'), id=quiz_id)
    if not is_student_enrolled(request.user, quiz.course):
        raise PermissionDenied("You must be enrolled in the course to take this assessment.")

    if not quiz.is_published:
        raise Http404("This quiz is currently unavailable.")

    # Questions and choices (strip out is_correct)
    questions = quiz.questions.all().prefetch_related('choices').order_by('ordering')
    if not questions.exists():
        messages.warning(request, "This quiz does not have any questions yet.")
        return redirect('learning:quiz_detail', quiz_id=quiz.id)

    return render(request, 'learning/quiz_take.html', {
        'quiz': quiz,
        'course': quiz.course,
        'questions': questions,
    })


@student_required
@require_POST
def quiz_submit(request, quiz_id):
    """Process student answers with server-side validation and scoring."""
    quiz = get_object_or_404(Quiz.objects.select_related('course'), id=quiz_id)
    if not is_student_enrolled(request.user, quiz.course):
        raise PermissionDenied("You must be enrolled in the course to submit this quiz.")

    questions = list(quiz.questions.all().prefetch_related('choices'))
    if not questions:
        raise Http404("Quiz has no questions.")

    correct_answers = 0
    total_questions = len(questions)

    with transaction.atomic():
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            student=request.user,
            submitted_at=timezone.now(),
            total_questions=total_questions
        )

        for q in questions:
            choice_id_str = request.POST.get(f'question_{q.id}')
            selected_choice = None
            is_correct = False

            if choice_id_str:
                try:
                    choice_id = int(choice_id_str)
                    # Verify choice belongs to question
                    selected_choice = q.choices.filter(id=choice_id).first()
                    if selected_choice and selected_choice.is_correct:
                        is_correct = True
                        correct_answers += 1
                except (ValueError, TypeError):
                    selected_choice = None

            AttemptAnswer.objects.create(
                attempt=attempt,
                question=q,
                selected_choice=selected_choice,
                is_correct=is_correct
            )

        percentage = round((correct_answers / total_questions) * 100, 1) if total_questions > 0 else 0.0
        passed = percentage >= quiz.passing_percentage

        attempt.score = correct_answers
        attempt.percentage = percentage
        attempt.passed = passed
        attempt.save()

    messages.success(request, f"Quiz submitted! Your score: {correct_answers}/{total_questions} ({percentage}%)")
    return redirect('learning:quiz_result', attempt_id=attempt.id)


@login_required
def quiz_result(request, attempt_id):
    """View quiz results with answer breakdown and explanations."""
    attempt = get_object_or_404(
        QuizAttempt.objects.select_related('quiz', 'quiz__course', 'student').prefetch_related(
            'answers__question', 'answers__question__choices', 'answers__selected_choice'
        ),
        id=attempt_id
    )

    # Permission check: Student who took it OR Teacher owner
    is_owner_teacher = (attempt.quiz.course.teacher_id == request.user.id)
    if not (attempt.student_id == request.user.id or is_owner_teacher):
        raise PermissionDenied("You do not have permission to view this quiz result.")

    answers = attempt.answers.all().order_by('question__ordering')

    return render(request, 'learning/quiz_result.html', {
        'attempt': attempt,
        'quiz': attempt.quiz,
        'course': attempt.quiz.course,
        'answers': answers,
        'is_owner_teacher': is_owner_teacher,
    })


@student_required
def quiz_history(request, quiz_id):
    """View all past attempts for a quiz by the current student."""
    quiz = get_object_or_404(Quiz.objects.select_related('course'), id=quiz_id)
    if not is_student_enrolled(request.user, quiz.course):
        raise PermissionDenied("You must be enrolled to view attempt history.")

    attempts = QuizAttempt.objects.filter(quiz=quiz, student=request.user).order_by('-submitted_at')

    return render(request, 'learning/quiz_history.html', {
        'quiz': quiz,
        'course': quiz.course,
        'attempts': attempts,
    })


@teacher_required
def teacher_quiz_analytics(request, quiz_id):
    """Instructor overview of all student quiz attempts and metrics."""
    quiz = get_object_or_404(Quiz.objects.select_related('course'), id=quiz_id)
    check_course_ownership(request.user, quiz.course)

    attempts = QuizAttempt.objects.filter(quiz=quiz).select_related('student').order_by('-submitted_at')

    total_attempts = attempts.count()
    avg_score = attempts.aggregate(Avg('percentage'))['percentage__avg'] or 0.0
    passed_count = attempts.filter(passed=True).count()
    pass_rate = round((passed_count / total_attempts * 100), 1) if total_attempts > 0 else 0.0

    return render(request, 'learning/teacher_quiz_analytics.html', {
        'quiz': quiz,
        'course': quiz.course,
        'attempts': attempts,
        'total_attempts': total_attempts,
        'avg_score': round(avg_score, 1),
        'pass_rate': pass_rate,
        'passed_count': passed_count,
    })

from django.contrib import admin
from .models import (
    Course, Lesson, Resource, Enrollment, LessonProgress,
    Quiz, Question, Choice, QuizAttempt, AttemptAnswer
)


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ('ordering', 'title', 'estimated_duration')
    ordering = ('ordering',)


class ResourceInline(admin.TabularInline):
    model = Resource
    extra = 0
    fields = ('title', 'file', 'external_url', 'uploaded_by')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'category', 'difficulty_level', 'status', 'created_at')
    list_filter = ('status', 'difficulty_level', 'category', 'created_at')
    search_fields = ('title', 'short_description', 'description', 'teacher__username', 'teacher__email')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [LessonInline, ResourceInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'ordering', 'estimated_duration', 'created_at')
    list_filter = ('course', 'created_at')
    search_fields = ('title', 'lesson_content', 'course__title')
    ordering = ('course', 'ordering')


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'lesson', 'uploaded_by', 'created_at')
    list_filter = ('course', 'created_at')
    search_fields = ('title', 'description', 'course__title')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at', 'active')
    list_filter = ('active', 'enrolled_at')
    search_fields = ('student__username', 'student__email', 'course__title')


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'lesson', 'is_completed', 'completed_at', 'updated_at')
    list_filter = ('is_completed', 'completed_at')
    search_fields = ('student__username', 'lesson__title')


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'quiz', 'ordering')
    list_filter = ('quiz',)
    search_fields = ('question_text', 'quiz__title')
    inlines = [ChoiceInline]


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'created_by', 'passing_percentage', 'is_published', 'created_at')
    list_filter = ('is_published', 'passing_percentage', 'created_at')
    search_fields = ('title', 'description', 'course__title')
    inlines = [QuestionInline]


class AttemptAnswerInline(admin.TabularInline):
    model = AttemptAnswer
    extra = 0
    readonly_fields = ('question', 'selected_choice', 'is_correct')


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'score', 'total_questions', 'percentage', 'passed', 'submitted_at')
    list_filter = ('passed', 'submitted_at')
    search_fields = ('student__username', 'quiz__title')
    inlines = [AttemptAnswerInline]
    readonly_fields = ('started_at', 'submitted_at')

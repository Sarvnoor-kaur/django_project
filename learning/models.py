import os
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.urls import reverse


def validate_resource_file(file):
    """Validate resource file extension, size, and header."""
    allowed_extensions = ['.pdf', '.zip', '.doc', '.docx', '.txt', '.pptx', '.ipynb']
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(f"File type '{ext}' is not supported. Allowed: {', '.join(allowed_extensions)}")
    
    # Check max file size (15 MB)
    max_size_mb = 15
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"File size exceeds limit of {max_size_mb}MB.")
    
    # Check PDF magic bytes if extension is .pdf
    if ext == '.pdf':
        first_bytes = file.read(5)
        file.seek(0)
        if first_bytes != b'%PDF-':
            raise ValidationError("Invalid PDF file format. Signature check failed.")


class Course(models.Model):
    """Course model supporting drafts, publishing, categories, and difficulty levels."""
    
    DIFFICULTY_BEGINNER = 'BEGINNER'
    DIFFICULTY_INTERMEDIATE = 'INTERMEDIATE'
    DIFFICULTY_ADVANCED = 'ADVANCED'
    
    DIFFICULTY_CHOICES = [
        (DIFFICULTY_BEGINNER, 'Beginner'),
        (DIFFICULTY_INTERMEDIATE, 'Intermediate'),
        (DIFFICULTY_ADVANCED, 'Advanced'),
    ]

    STATUS_DRAFT = 'DRAFT'
    STATUS_PUBLISHED = 'PUBLISHED'
    
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PUBLISHED, 'Published'),
    ]

    CATEGORY_CHOICES = [
        ('Web Development', 'Web Development'),
        ('Data Science & AI', 'Data Science & AI'),
        ('Mobile App Development', 'Mobile App Development'),
        ('Cybersecurity', 'Cybersecurity'),
        ('Cloud & DevOps', 'Cloud & DevOps'),
        ('Programming Fundamentals', 'Programming Fundamentals'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    short_description = models.CharField(max_length=300)
    description = models.TextField()
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='Web Development')
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default=DIFFICULTY_BEGINNER)
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'category']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or 'course'
            slug = base_slug
            counter = 1
            while Course.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def is_published(self):
        return self.status == self.STATUS_PUBLISHED

    def get_absolute_url(self):
        return reverse('learning:course_detail', kwargs={'slug': self.slug})


class Lesson(models.Model):
    """Course lesson with sequence ordering and protected access."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True)
    short_description = models.CharField(max_length=300, blank=True)
    lesson_content = models.TextField()
    video_url = models.URLField(blank=True, null=True, help_text="Optional YouTube or hosted video URL")
    estimated_duration = models.PositiveIntegerField(default=10, help_text="Duration in minutes")
    ordering = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ordering', 'created_at']
        constraints = [
            models.UniqueConstraint(fields=['course', 'ordering'], name='unique_course_lesson_order')
        ]

    def __str__(self):
        return f"{self.course.title} - L{self.ordering}: {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or f"lesson-{self.ordering}"
            slug = base_slug
            counter = 1
            while Lesson.objects.filter(course=self.course, slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Resource(models.Model):
    """Downloadable learning resource (PDF, guides, slides)."""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='resources')
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name='resources')
    file = models.FileField(upload_to='course_resources/', validators=[validate_resource_file], blank=True, null=True)
    external_url = models.URLField(blank=True, null=True, help_text="Optional external link or documentation")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploaded_resources')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.course.title})"

    def clean(self):
        if not self.file and not self.external_url:
            raise ValidationError("Either a downloadable file or an external resource URL must be provided.")
        if self.lesson and self.lesson.course_id != self.course_id:
            raise ValidationError("The attached lesson must belong to the specified course.")


class Enrollment(models.Model):
    """Enrollment tracking connecting a student to a course."""
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-enrolled_at']
        constraints = [
            models.UniqueConstraint(fields=['student', 'course'], name='unique_student_course_enrollment')
        ]

    def __str__(self):
        return f"{self.student.username} -> {self.course.title}"


class LessonProgress(models.Model):
    """Tracks completion status of a lesson for an enrolled student."""
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress_records')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'lesson'], name='unique_student_lesson_progress')
        ]

    def __str__(self):
        status = "Completed" if self.is_completed else "Incomplete"
        return f"{self.student.username} - {self.lesson.title}: {status}"


class Quiz(models.Model):
    """Course assessment quiz."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_quizzes')
    passing_percentage = models.PositiveIntegerField(default=70, help_text="Minimum percentage required to pass")
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.course.title})"

    def total_questions_count(self):
        return self.questions.count()


class Question(models.Model):
    """Multiple choice question in a quiz."""
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    ordering = models.PositiveIntegerField(default=1)
    explanation = models.TextField(blank=True, help_text="Educational explanation displayed after submission")

    class Meta:
        ordering = ['ordering', 'id']

    def __str__(self):
        return f"Q{self.ordering}: {self.question_text[:50]}"


class Choice(models.Model):
    """Answer option for a quiz question."""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.choice_text} ({'Correct' if self.is_correct else 'Incorrect'})"


class QuizAttempt(models.Model):
    """Student submission for an assessment quiz."""
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    percentage = models.FloatField(default=0.0)
    passed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} ({self.percentage}%)"


class AttemptAnswer(models.Model):
    """Individual answer submitted in a quiz attempt."""
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='attempt_answers')
    selected_choice = models.ForeignKey(Choice, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    is_correct = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['attempt', 'question'], name='unique_attempt_question_answer')
        ]

    def __str__(self):
        return f"Attempt {self.attempt.id} - Q{self.question_id}: {'Correct' if self.is_correct else 'Wrong'}"

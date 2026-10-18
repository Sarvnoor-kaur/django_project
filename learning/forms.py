from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError
from .models import Course, Lesson, Resource, Quiz, Question, Choice


class CourseForm(forms.ModelForm):
    """Teacher form for creating and updating courses."""
    class Meta:
        model = Course
        fields = [
            'title', 'short_description', 'description',
            'category', 'difficulty_level', 'thumbnail', 'status'
        ]
        widgets = {
            'short_description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'A concise overview for cards...'}),
            'description': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Comprehensive curriculum overview...'}),
        }


class LessonForm(forms.ModelForm):
    """Teacher form for creating and updating lessons."""
    class Meta:
        model = Lesson
        fields = [
            'title', 'short_description', 'lesson_content',
            'video_url', 'estimated_duration', 'ordering'
        ]
        widgets = {
            'short_description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Brief summary of the lesson...'}),
            'lesson_content': forms.Textarea(attrs={'rows': 8, 'placeholder': 'Write educational markdown/text content...'}),
            'video_url': forms.URLInput(attrs={'placeholder': 'https://www.youtube.com/watch?v=...'}),
        }


class ResourceForm(forms.ModelForm):
    """Teacher form for uploading course/lesson resources."""
    class Meta:
        model = Resource
        fields = ['title', 'description', 'lesson', 'file', 'external_url']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Resource summary or instructions...'}),
            'external_url': forms.URLInput(attrs={'placeholder': 'https://...'}),
        }

    def __init__(self, *args, **kwargs):
        course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        if course:
            self.fields['lesson'].queryset = course.lessons.all()
            self.fields['lesson'].empty_label = "General Course Resource (No specific lesson)"


class QuizForm(forms.ModelForm):
    """Teacher form for creating and editing assessment quizzes."""
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'passing_percentage', 'is_published']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Assessment instructions, topics covered...'}),
        }


class QuestionForm(forms.ModelForm):
    """Teacher form for creating and updating quiz questions."""
    class Meta:
        model = Question
        fields = ['question_text', 'ordering', 'explanation']
        widgets = {
            'question_text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter the assessment question here...'}),
            'explanation': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Explanation displayed to students after submitting answers...'}),
        }


class BaseChoiceFormSet(BaseInlineFormSet):
    """Formset validation ensuring multiple choices and exactly one correct answer."""
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        choices = []
        correct_count = 0
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            choice_text = form.cleaned_data.get('choice_text')
            is_correct = form.cleaned_data.get('is_correct', False)
            if choice_text:
                choices.append(choice_text)
                if is_correct:
                    correct_count += 1

        if len(choices) < 2:
            raise ValidationError("A question must have at least 2 choices.")
        if correct_count != 1:
            raise ValidationError(f"Exactly one choice must be marked as correct (currently {correct_count} marked).")


ChoiceFormSet = inlineformset_factory(
    Question, Choice,
    fields=['choice_text', 'is_correct'],
    extra=4,
    can_delete=True,
    formset=BaseChoiceFormSet
)

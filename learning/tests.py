import os
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import CustomUser
from learning.models import (
    Course, Lesson, Resource, Enrollment, LessonProgress,
    Quiz, Question, Choice, QuizAttempt, AttemptAnswer
)


class LearningPlatformTests(TestCase):
    """Comprehensive test suite for SmartEdu LMS Phase 2."""

    def setUp(self):
        # Create Teacher 1
        self.teacher1 = CustomUser.objects.create_user(
            username='prof_smith',
            email='smith@smartedu.com',
            password='Password123!',
            role=CustomUser.TEACHER,
            first_name='John',
            last_name='Smith'
        )

        # Create Teacher 2
        self.teacher2 = CustomUser.objects.create_user(
            username='prof_davis',
            email='davis@smartedu.com',
            password='Password123!',
            role=CustomUser.TEACHER,
            first_name='Alan',
            last_name='Davis'
        )

        # Create Student 1
        self.student1 = CustomUser.objects.create_user(
            username='student_alice',
            email='alice@smartedu.com',
            password='Password123!',
            role=CustomUser.STUDENT,
            first_name='Alice',
            last_name='Walker'
        )

        # Create Student 2
        self.student2 = CustomUser.objects.create_user(
            username='student_bob',
            email='bob@smartedu.com',
            password='Password123!',
            role=CustomUser.STUDENT,
            first_name='Bob',
            last_name='Miller'
        )

        # Create Published Course by Teacher 1
        self.course_published = Course.objects.create(
            title='Python Fundamentals',
            short_description='Master Python 3 syntax and data structures.',
            description='Detailed Python programming curriculum for software engineers.',
            category='Programming Fundamentals',
            difficulty_level=Course.DIFFICULTY_BEGINNER,
            teacher=self.teacher1,
            status=Course.STATUS_PUBLISHED
        )

        # Create Draft Course by Teacher 1
        self.course_draft = Course.objects.create(
            title='Draft Data Analytics',
            short_description='Under development.',
            description='Coming soon analytics syllabus.',
            category='Data Science & AI',
            difficulty_level=Course.DIFFICULTY_INTERMEDIATE,
            teacher=self.teacher1,
            status=Course.STATUS_DRAFT
        )

        # Add Lessons to Published Course
        self.lesson1 = Lesson.objects.create(
            course=self.course_published,
            title='Introduction to Variables',
            short_description='Basic data types and memory.',
            lesson_content='In Python, variables are dynamically typed references.',
            ordering=1,
            estimated_duration=10
        )

        self.lesson2 = Lesson.objects.create(
            course=self.course_published,
            title='Control Flow & Loops',
            short_description='If statements and while loops.',
            lesson_content='Loops allow repeated execution of code blocks.',
            ordering=2,
            estimated_duration=15
        )

        # Create Quiz for Published Course
        self.quiz = Quiz.objects.create(
            course=self.course_published,
            title='Python Basics Assessment',
            description='Test your understanding of variables and loops.',
            created_by=self.teacher1,
            passing_percentage=50,
            is_published=True
        )

        # Question 1: 1 correct choice
        self.q1 = Question.objects.create(
            quiz=self.quiz,
            question_text='What is the output of print(2 + 2)?',
            ordering=1,
            explanation='2 + 2 arithmetic addition evaluates to integer 4.'
        )
        self.q1_c1 = Choice.objects.create(question=self.q1, choice_text='4', is_correct=True)
        self.q1_c2 = Choice.objects.create(question=self.q1, choice_text='22', is_correct=False)
        self.q1_c3 = Choice.objects.create(question=self.q1, choice_text='Error', is_correct=False)

        # Question 2: 1 correct choice
        self.q2 = Question.objects.create(
            quiz=self.quiz,
            question_text='Which keyword is used to define a function in Python?',
            ordering=2,
            explanation='The def keyword is used to define functions in Python.'
        )
        self.q2_c1 = Choice.objects.create(question=self.q2, choice_text='def', is_correct=True)
        self.q2_c2 = Choice.objects.create(question=self.q2, choice_text='function', is_correct=False)
        self.q2_c3 = Choice.objects.create(question=self.q2, choice_text='fun', is_correct=False)

    # --------------------------------------------------------------------------
    # 1. Course Management Tests
    # --------------------------------------------------------------------------

    def test_teacher_can_create_course(self):
        """Instructors can create courses through the interface."""
        self.client.force_login(self.teacher1)
        response = self.client.post(reverse('learning:course_create'), {
            'title': 'Advanced Django SaaS',
            'short_description': 'Enterprise web platform design.',
            'description': 'Full architecture guide.',
            'category': 'Web Development',
            'difficulty_level': 'ADVANCED',
            'status': 'PUBLISHED'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Course.objects.filter(title='Advanced Django SaaS', teacher=self.teacher1).exists())

    def test_student_cannot_create_or_edit_course(self):
        """Students must be denied access to course creation and edit routes."""
        self.client.force_login(self.student1)
        res_create = self.client.get(reverse('learning:course_create'))
        self.assertEqual(res_create.status_code, 403)

        res_edit = self.client.get(reverse('learning:course_edit', kwargs={'slug': self.course_published.slug}))
        self.assertEqual(res_edit.status_code, 403)

    def test_teacher_cannot_modify_other_teachers_course(self):
        """A teacher must not be able to edit or delete courses belonging to another teacher."""
        self.client.force_login(self.teacher2)
        res_edit = self.client.get(reverse('learning:course_edit', kwargs={'slug': self.course_published.slug}))
        self.assertEqual(res_edit.status_code, 403)

        res_del = self.client.post(reverse('learning:course_delete', kwargs={'slug': self.course_published.slug}))
        self.assertEqual(res_del.status_code, 403)

    def test_draft_courses_hidden_from_students(self):
        """Draft courses should not appear in course catalog for students."""
        self.client.force_login(self.student1)
        response = self.client.get(reverse('learning:course_list'))
        self.assertContains(response, self.course_published.title)
        self.assertNotContains(response, self.course_draft.title)

        # Direct access to draft detail returns 404 for students
        detail_res = self.client.get(reverse('learning:course_detail', kwargs={'slug': self.course_draft.slug}))
        self.assertEqual(detail_res.status_code, 404)

    def test_course_search_and_filtering(self):
        """Catalog search and category filters filter results correctly."""
        response = self.client.get(reverse('learning:course_list'), {'q': 'Python'})
        self.assertContains(response, 'Python Fundamentals')

        response_filtered = self.client.get(reverse('learning:course_list'), {'category': 'Cybersecurity'})
        self.assertNotContains(response_filtered, 'Python Fundamentals')

    # --------------------------------------------------------------------------
    # 2. Lessons & Resources Tests
    # --------------------------------------------------------------------------

    def test_lesson_ordering(self):
        """Lessons within a course are retrieved in correct ordering."""
        lessons = list(self.course_published.lessons.all())
        self.assertEqual(lessons[0].ordering, 1)
        self.assertEqual(lessons[1].ordering, 2)

    def test_enrollment_required_for_lesson_access(self):
        """Unenrolled student cannot access lesson content."""
        self.client.force_login(self.student1)
        response = self.client.get(reverse('learning:lesson_detail', kwargs={
            'course_slug': self.course_published.slug,
            'lesson_slug': self.lesson1.slug
        }))
        self.assertEqual(response.status_code, 403)

    def test_enrolled_student_can_access_lesson(self):
        """Enrolled student can view lesson content."""
        Enrollment.objects.create(student=self.student1, course=self.course_published, active=True)
        self.client.force_login(self.student1)
        response = self.client.get(reverse('learning:lesson_detail', kwargs={
            'course_slug': self.course_published.slug,
            'lesson_slug': self.lesson1.slug
        }))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Introduction to Variables')

    def test_private_resource_download_protection(self):
        """Unauthorized students cannot download course resources."""
        # Create a sample valid PDF resource
        pdf_content = b"%PDF-1.4\n%test pdf content"
        pdf_file = SimpleUploadedFile("sample.pdf", pdf_content, content_type="application/pdf")
        resource = Resource.objects.create(
            title='Python CheatSheet',
            course=self.course_published,
            file=pdf_file,
            uploaded_by=self.teacher1
        )

        # Unenrolled student attempt
        self.client.force_login(self.student1)
        res_unauthorized = self.client.get(reverse('learning:download_resource', kwargs={'resource_id': resource.id}))
        self.assertEqual(res_unauthorized.status_code, 403)

        # Enrolled student attempt
        Enrollment.objects.create(student=self.student1, course=self.course_published, active=True)
        res_authorized = self.client.get(reverse('learning:download_resource', kwargs={'resource_id': resource.id}))
        self.assertEqual(res_authorized.status_code, 200)

    # --------------------------------------------------------------------------
    # 3. Enrollment & Progress Tests
    # --------------------------------------------------------------------------

    def test_student_enrollment_workflow(self):
        """Student can successfully enroll in a published course."""
        self.client.force_login(self.student1)
        response = self.client.post(reverse('learning:enroll_course', kwargs={'slug': self.course_published.slug}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Enrollment.objects.filter(student=self.student1, course=self.course_published, active=True).exists())

    def test_duplicate_enrollment_prevented(self):
        """Duplicate enrollment requests do not create duplicate database records."""
        self.client.force_login(self.student1)
        self.client.post(reverse('learning:enroll_course', kwargs={'slug': self.course_published.slug}))
        self.client.post(reverse('learning:enroll_course', kwargs={'slug': self.course_published.slug}))
        count = Enrollment.objects.filter(student=self.student1, course=self.course_published).count()
        self.assertEqual(count, 1)

    def test_cannot_enroll_in_draft_course(self):
        """Students cannot enroll in draft courses."""
        self.client.force_login(self.student1)
        response = self.client.post(reverse('learning:enroll_course', kwargs={'slug': self.course_draft.slug}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Enrollment.objects.filter(student=self.student1, course=self.course_draft).exists())

    def test_teacher_cannot_enroll_as_student(self):
        """Instructors are prevented from taking student enrollment actions."""
        self.client.force_login(self.teacher1)
        response = self.client.post(reverse('learning:enroll_course', kwargs={'slug': self.course_published.slug}))
        self.assertEqual(response.status_code, 403)

    def test_lesson_progress_toggle(self):
        """Enrolled student can toggle lesson completion and calculate course progress."""
        Enrollment.objects.create(student=self.student1, course=self.course_published, active=True)
        self.client.force_login(self.student1)

        # Mark lesson 1 completed
        self.client.post(reverse('learning:toggle_lesson_progress', kwargs={'lesson_id': self.lesson1.id}))
        progress = LessonProgress.objects.get(student=self.student1, lesson=self.lesson1)
        self.assertTrue(progress.is_completed)

        # Check My Courses progress
        res = self.client.get(reverse('learning:my_courses'))
        self.assertContains(res, '50%')  # 1 of 2 lessons = 50%

    def test_another_student_progress_isolated(self):
        """Student 2's progress does not affect Student 1."""
        Enrollment.objects.create(student=self.student1, course=self.course_published, active=True)
        Enrollment.objects.create(student=self.student2, course=self.course_published, active=True)

        LessonProgress.objects.create(student=self.student1, lesson=self.lesson1, is_completed=True)
        
        self.client.force_login(self.student2)
        res = self.client.get(reverse('learning:my_courses'))
        self.assertContains(res, '0%')  # Student 2 has completed 0 lessons

    # --------------------------------------------------------------------------
    # 4. Quiz & Assessment Tests
    # --------------------------------------------------------------------------

    def test_correct_answers_not_leaked_in_quiz_take(self):
        """The quiz taking page must never include is_correct in the HTML output."""
        Enrollment.objects.create(student=self.student1, course=self.course_published, active=True)
        self.client.force_login(self.student1)

        response = self.client.get(reverse('learning:quiz_take', kwargs={'quiz_id': self.quiz.id}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'is_correct')
        self.assertNotContains(response, 'True')

    def test_quiz_scoring_and_pass_result(self):
        """Server correctly calculates scores and awards pass status."""
        Enrollment.objects.create(student=self.student1, course=self.course_published, active=True)
        self.client.force_login(self.student1)

        # Submit 2 correct answers
        response = self.client.post(reverse('learning:quiz_submit', kwargs={'quiz_id': self.quiz.id}), {
            f'question_{self.q1.id}': self.q1_c1.id,  # '4' (correct)
            f'question_{self.q2.id}': self.q2_c1.id,  # 'def' (correct)
        })
        self.assertEqual(response.status_code, 302)

        attempt = QuizAttempt.objects.filter(student=self.student1, quiz=self.quiz).first()
        self.assertIsNotNone(attempt)
        self.assertEqual(attempt.score, 2)
        self.assertEqual(attempt.total_questions, 2)
        self.assertEqual(attempt.percentage, 100.0)
        self.assertTrue(attempt.passed)

    def test_quiz_failing_result(self):
        """Submitting wrong answers accurately records fail status."""
        Enrollment.objects.create(student=self.student1, course=self.course_published, active=True)
        self.client.force_login(self.student1)

        # Submit 2 wrong answers
        self.client.post(reverse('learning:quiz_submit', kwargs={'quiz_id': self.quiz.id}), {
            f'question_{self.q1.id}': self.q1_c2.id,  # '22' (wrong)
            f'question_{self.q2.id}': self.q2_c2.id,  # 'function' (wrong)
        })

        attempt = QuizAttempt.objects.filter(student=self.student1, quiz=self.quiz).first()
        self.assertEqual(attempt.score, 0)
        self.assertEqual(attempt.percentage, 0.0)
        self.assertFalse(attempt.passed)

    def test_unauthorized_student_cannot_view_others_quiz_result(self):
        """Student 2 cannot view Student 1's private quiz attempt."""
        attempt = QuizAttempt.objects.create(
            quiz=self.quiz,
            student=self.student1,
            score=2,
            total_questions=2,
            percentage=100.0,
            passed=True
        )

        self.client.force_login(self.student2)
        response = self.client.get(reverse('learning:quiz_result', kwargs={'attempt_id': attempt.id}))
        self.assertEqual(response.status_code, 403)

    # --------------------------------------------------------------------------
    # 5. Dashboard Statistics Tests
    # --------------------------------------------------------------------------

    def test_student_dashboard_real_data(self):
        """Student dashboard accurately reflects enrollments and completions."""
        Enrollment.objects.create(student=self.student1, course=self.course_published, active=True)
        LessonProgress.objects.create(student=self.student1, lesson=self.lesson1, is_completed=True)

        self.client.force_login(self.student1)
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_courses'], 1)
        self.assertEqual(response.context['total_completed_lessons'], 1)
        self.assertEqual(response.context['overall_progress'], 50)

    def test_teacher_dashboard_scoped_to_teacher(self):
        """Teacher dashboard includes only courses created by that teacher."""
        self.client.force_login(self.teacher1)
        response = self.client.get(reverse('teacher_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_courses'], 2)  # Published + Draft
        self.assertEqual(response.context['published_courses'], 1)
        self.assertEqual(response.context['draft_courses'], 1)

        # Teacher 2 has 0 courses
        self.client.force_login(self.teacher2)
        res_t2 = self.client.get(reverse('teacher_dashboard'))
        self.assertEqual(res_t2.context['total_courses'], 0)

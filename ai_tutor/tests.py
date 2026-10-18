"""
Automated unit and integration test suite for SmartEdu Phase 3:
Demo AI Tutor, Personalized Learning Recommendations, Analytics, and Teacher Drafting.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model

from django.utils import timezone
from accounts.models import CustomUser
from learning.models import Course, Lesson, Enrollment, LessonProgress, Quiz, Question, Choice, QuizAttempt
from ai_tutor.models import Conversation, Message
from ai_tutor.knowledge_base import KNOWLEDGE_BASE
from ai_tutor.services.ai_engine import (
    normalize_text, detect_intent, find_topic_match, process_user_query, generate_fallback_response
)
from ai_tutor.services.lesson_assistant import (
    verify_user_lesson_access, summarize_lesson_content,
    extract_lesson_key_points, generate_lesson_revision_questions
)
from ai_tutor.services.recommendations import get_student_recommendations
from ai_tutor.services.analytics import get_student_analytics, get_teacher_analytics
from ai_tutor.services.teacher_assistant import (
    draft_lesson_summary, draft_lesson_key_points, draft_revision_questions, draft_topic_outline
)

User = get_user_model()


class AIEngineUnitTests(TestCase):
    """Test the deterministic topic and intent matching engine."""

    def test_text_normalization(self):
        raw = "   Explain   DBMS   Normalization, Please!!  "
        normalized = normalize_text(raw)
        self.assertEqual(normalized, "explain dbms normalization please")

    def test_intent_detection(self):
        self.assertEqual(detect_intent("explain normalization in dbms"), "explain")
        self.assertEqual(detect_intent("summarize this lesson for me"), "summarize")
        self.assertEqual(detect_intent("give me revision questions on python"), "revision_questions")
        self.assertEqual(detect_intent("what are the key points of computer networks"), "key_points")
        self.assertEqual(detect_intent("how should i study operating systems"), "study_strategies")

    def test_topic_matching_supported(self):
        key, data, score = find_topic_match("explain dbms normalization in sql")
        self.assertIsNotNone(key)
        self.assertEqual(key, "dbms_normalization")
        self.assertGreater(score, 3.0)

    def test_topic_matching_fallback_for_unknown(self):
        key, data, score = find_topic_match("quantum teleportation in astrophysics")
        self.assertIsNone(key)
        self.assertIsNone(data)

    def test_empty_message_validation(self):
        res = process_user_query("   ")
        self.assertFalse(res['success'])
        self.assertIn("Please enter a question", res['response'])

    def test_overlong_message_validation(self):
        long_query = "word " * 300
        res = process_user_query(long_query)
        self.assertFalse(res['success'])
        self.assertIn("1,000-character limit", res['response'])

    def test_process_valid_topic_query(self):
        res = process_user_query("Give me revision questions on Python")
        self.assertTrue(res['success'])
        self.assertEqual(res['intent'], "revision_questions")
        self.assertIn("Question", res['response'])


class LessonAssistantAndPrivacyTests(TestCase):
    """Test lesson context retrieval, summarization, and security authorization."""

    def setUp(self):
        self.teacher1 = User.objects.create_user(username='prof1', password='password123', role=CustomUser.TEACHER)
        self.teacher2 = User.objects.create_user(username='prof2', password='password123', role=CustomUser.TEACHER)
        self.student1 = User.objects.create_user(username='stud1', password='password123', role=CustomUser.STUDENT)
        self.student2 = User.objects.create_user(username='stud2', password='password123', role=CustomUser.STUDENT)

        self.course = Course.objects.create(
            title="Django Advanced",
            teacher=self.teacher1,
            status=Course.STATUS_PUBLISHED
        )
        self.lesson = Lesson.objects.create(
            course=self.course,
            title="Django ORM Deep Dive",
            ordering=1,
            lesson_content=(
                "Django ORM provides an object relational mapping layer. "
                "It abstracts database queries into clean Python objects. "
                "QuerySets are evaluated lazily to maximize database performance. "
                "Developers can use prefetch_related and select_related to eliminate N+1 bottlenecks. "
                "Transactions ensure atomic execution across multiple table updates."
            )
        )
        # Student1 is enrolled; Student2 is NOT enrolled
        Enrollment.objects.create(student=self.student1, course=self.course, active=True)

    def test_authorized_student_access(self):
        # Should not raise
        verify_user_lesson_access(self.student1, self.lesson)

    def test_authorized_teacher_owner_access(self):
        # Course owner should not raise
        verify_user_lesson_access(self.teacher1, self.lesson)

    def test_unauthorized_student_access_raises_permission_denied(self):
        with self.assertRaises(PermissionDenied):
            verify_user_lesson_access(self.student2, self.lesson)

    def test_lesson_summarization_grounded(self):
        summary = summarize_lesson_content(self.lesson)
        self.assertTrue(summary['success'])
        self.assertIn("Django ORM provides", summary['summary'])

    def test_lesson_summarization_insufficient_content(self):
        short_lesson = Lesson.objects.create(course=self.course, title="Short", ordering=2, lesson_content="Too short.")
        summary = summarize_lesson_content(short_lesson)
        self.assertFalse(summary['success'])
        self.assertIn("content is brief", summary['summary'])

    def test_lesson_revision_questions(self):
        res = generate_lesson_revision_questions(self.lesson)
        self.assertTrue(res['success'])
        self.assertIn("Question 1", res['questions'])


class ConversationPrivacyTests(TestCase):
    """Test conversation persistence and object-level permissions."""

    def setUp(self):
        self.student1 = User.objects.create_user(username='alice', password='password123', role=CustomUser.STUDENT)
        self.student2 = User.objects.create_user(username='bob', password='password123', role=CustomUser.STUDENT)
        self.conv = Conversation.objects.create(user=self.student1, title="Alice's Session")

    def test_owner_can_access_conversation(self):
        client = Client()
        client.login(username='alice', password='password123')
        response = client.get(reverse('ai_tutor:tutor_chat', kwargs={'conversation_id': self.conv.id}))
        self.assertEqual(response.status_code, 200)

    def test_unauthorized_user_blocked_from_another_conversation(self):
        client = Client()
        client.login(username='bob', password='password123')
        response = client.get(reverse('ai_tutor:tutor_chat', kwargs={'conversation_id': self.conv.id}))
        self.assertEqual(response.status_code, 403)

    def test_send_message_updates_conversation(self):
        client = Client()
        client.login(username='alice', password='password123')
        response = client.post(
            reverse('ai_tutor:send_message', kwargs={'conversation_id': self.conv.id}),
            {'message': "Explain normalization in DBMS"}
        )
        self.assertEqual(response.status_code, 302)
        # Should now have user message and assistant message
        self.assertEqual(self.conv.messages.count(), 2)
        assistant_msg = self.conv.messages.filter(role=Message.ROLE_ASSISTANT).first()
        self.assertIn("Normalization", assistant_msg.content)


class RecommendationAndAnalyticsTests(TestCase):
    """Test transparent recommendations and database-backed analytics."""

    def setUp(self):
        self.teacher = User.objects.create_user(username='prof_smith', password='pass', role=CustomUser.TEACHER)
        self.student = User.objects.create_user(username='charlie', password='pass', role=CustomUser.STUDENT)

        self.course = Course.objects.create(
            title="Database Systems",
            teacher=self.teacher,
            status=Course.STATUS_PUBLISHED,
            category='Web Development'
        )
        self.l1 = Lesson.objects.create(course=self.course, title="Intro to SQL", ordering=1, lesson_content="Content...")
        self.l2 = Lesson.objects.create(course=self.course, title="Indexes & Keys", ordering=2, lesson_content="Content...")

        Enrollment.objects.create(student=self.student, course=self.course, active=True)
        # Mark Lesson 1 as completed
        LessonProgress.objects.create(student=self.student, lesson=self.l1, is_completed=True)

        # Create Quiz
        self.quiz = Quiz.objects.create(course=self.course, title="SQL Basics Quiz", created_by=self.teacher, passing_percentage=60)
        # Failed attempt
        QuizAttempt.objects.create(
            student=self.student,
            quiz=self.quiz,
            score=1,
            total_questions=3,
            percentage=33.3,
            passed=False,
            submitted_at=timezone.now()
        )

    def test_student_recommendations_incomplete_lesson(self):
        recs = get_student_recommendations(self.student)
        self.assertTrue(len(recs) > 0)
        # Top rec should recommend Lesson 2
        titles = [r['title'] for r in recs]
        self.assertTrue(any("Lesson 2: Indexes & Keys" in t for t in titles))
        # Should also recommend reviewing the failed quiz
        badges = [r['badge'] for r in recs]
        self.assertIn("Quiz Revision", badges)

    def test_student_analytics_calculation(self):
        analytics = get_student_analytics(self.student)
        self.assertEqual(analytics['total_enrolled_courses'], 1)
        self.assertEqual(analytics['total_completed_lessons'], 1)
        self.assertEqual(analytics['total_lessons_all_enrolled'], 2)
        self.assertEqual(analytics['overall_progress'], 50)
        self.assertEqual(analytics['total_quiz_attempts'], 1)
        self.assertEqual(analytics['passed_attempts'], 0)
        self.assertEqual(analytics['failed_attempts'], 1)

    def test_teacher_analytics_scoped(self):
        teacher_analytics = get_teacher_analytics(self.teacher)
        self.assertEqual(teacher_analytics['total_courses'], 1)
        self.assertEqual(teacher_analytics['total_enrollments'], 1)
        self.assertEqual(teacher_analytics['total_lessons'], 2)
        self.assertEqual(teacher_analytics['total_attempts_count'], 1)


class TeacherDraftingTests(TestCase):
    """Test instructor AI drafting studio."""

    def setUp(self):
        self.teacher1 = User.objects.create_user(username='t1', password='password123', role=CustomUser.TEACHER)
        self.teacher2 = User.objects.create_user(username='t2', password='password123', role=CustomUser.TEACHER)
        self.course = Course.objects.create(title="Operating Systems", teacher=self.teacher1)
        self.lesson = Lesson.objects.create(
            course=self.course,
            title="Deadlocks in OS",
            ordering=1,
            lesson_content=(
                "Deadlock describes a state in computer systems where processes are permanently blocked. "
                "This occurs when each process holds a resource while requesting another held by another process. "
                "The four Coffman conditions are mutual exclusion, hold and wait, no preemption, and circular wait. "
                "Operating systems resolve deadlocks via prevention, avoidance with Banker's algorithm, or recovery."
            )
        )

    def test_teacher_summary_draft(self):
        res = draft_lesson_summary(self.teacher1, self.lesson)
        self.assertTrue(res['success'])
        self.assertIn("Summary of Deadlocks in OS", res['draft'])

    def test_teacher_key_points_draft(self):
        res = draft_lesson_key_points(self.teacher1, self.lesson)
        self.assertTrue(res['success'])
        self.assertIn("Key Learning Points", res['draft'])

    def test_teacher_cannot_draft_other_teacher_lesson(self):
        with self.assertRaises(PermissionDenied):
            draft_lesson_summary(self.teacher2, self.lesson)

    def test_draft_topic_outline(self):
        res = draft_topic_outline(self.teacher1, "Operating Systems")
        self.assertTrue(res['success'])
        self.assertIn("Proposed Curriculum Outline", res['draft'])

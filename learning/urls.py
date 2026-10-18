from django.urls import path
from . import views

app_name = 'learning'

urlpatterns = [
    # Course Catalog & Discovery
    path('courses/', views.course_list, name='course_list'),
    path('my-courses/', views.my_courses, name='my_courses'),
    
    # Teacher Course Management
    path('manage/courses/', views.teacher_course_list, name='teacher_course_list'),
    path('manage/courses/create/', views.course_create, name='course_create'),
    path('courses/<slug:slug>/', views.course_detail, name='course_detail'),
    path('courses/<slug:slug>/edit/', views.course_edit, name='course_edit'),
    path('courses/<slug:slug>/toggle-status/', views.course_toggle_status, name='course_toggle_status'),
    path('courses/<slug:slug>/delete/', views.course_delete, name='course_delete'),

    # Enrollment
    path('courses/<slug:slug>/enroll/', views.enroll_course, name='enroll_course'),
    path('courses/<slug:slug>/unenroll/', views.unenroll_course, name='unenroll_course'),

    # Lessons
    path('courses/<slug:course_slug>/lessons/create/', views.lesson_create, name='lesson_create'),
    path('courses/<slug:course_slug>/lessons/<slug:lesson_slug>/', views.lesson_detail, name='lesson_detail'),
    path('courses/<slug:course_slug>/lessons/<slug:lesson_slug>/edit/', views.lesson_edit, name='lesson_edit'),
    path('courses/<slug:course_slug>/lessons/<slug:lesson_slug>/delete/', views.lesson_delete, name='lesson_delete'),
    path('lessons/<int:lesson_id>/toggle-progress/', views.toggle_lesson_progress, name='toggle_lesson_progress'),

    # Resources
    path('courses/<slug:course_slug>/resources/', views.resource_list, name='resource_list'),
    path('courses/<slug:course_slug>/resources/upload/', views.resource_create, name='resource_create'),
    path('courses/<slug:course_slug>/resources/<int:resource_id>/delete/', views.resource_delete, name='resource_delete'),
    path('resources/<int:resource_id>/download/', views.download_resource, name='download_resource'),

    # Quizzes
    path('courses/<slug:course_slug>/quizzes/', views.quiz_list, name='quiz_list'),
    path('courses/<slug:course_slug>/quizzes/create/', views.quiz_create, name='quiz_create'),
    path('quizzes/<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('quizzes/<int:quiz_id>/edit/', views.quiz_edit, name='quiz_edit'),
    path('quizzes/<int:quiz_id>/delete/', views.quiz_delete, name='quiz_delete'),
    
    # Quiz Questions
    path('quizzes/<int:quiz_id>/questions/create/', views.question_create, name='question_create'),
    path('questions/<int:question_id>/edit/', views.question_edit, name='question_edit'),
    path('questions/<int:question_id>/delete/', views.question_delete, name='question_delete'),

    # Quiz Taking & Results
    path('quizzes/<int:quiz_id>/take/', views.quiz_take, name='quiz_take'),
    path('quizzes/<int:quiz_id>/submit/', views.quiz_submit, name='quiz_submit'),
    path('quiz-attempts/<int:attempt_id>/', views.quiz_result, name='quiz_result'),
    path('quizzes/<int:quiz_id>/history/', views.quiz_history, name='quiz_history'),
    path('quizzes/<int:quiz_id>/analytics/', views.teacher_quiz_analytics, name='teacher_quiz_analytics'),
]

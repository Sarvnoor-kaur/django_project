# SmartEdu — Smart Education Platform

A modern, responsive, and secure Learning Management System (LMS) built with Django 5 and a premium SaaS aesthetic.

---

## 🚀 Key Features (Phase 1 & Phase 2)

### 1. Authentication & Role-Based Access Control
- Custom User Model (`accounts.CustomUser`) supporting **Student** and **Teacher** roles.
- Interactive dual-role registration with dedicated forms and validation.
- Role-scoped dashboards and profile management.

### 2. Course Discovery & Curriculum Management
- **Course Catalog**: Filter by category, difficulty level (Beginner, Intermediate, Advanced), full-text search, and pagination.
- **Teacher Tools**: Create, edit, publish/unpublish drafts, and delete courses.
- **Lesson Management**: Sequenced ordering, lecture content, and video URLs.

### 3. Protected Educational Resources & Media
- Upload PDF lecture notes, code archives, slides, and reference links.
- Extension validation and PDF signature verification (`%PDF-`).
- **Protected Downloads**: Direct media links are blocked; private resources are securely streamed via permission-checked views (`/learning/resources/<id>/download/`) verifying active enrollment.

### 4. Progress Tracking & Assessments
- Student course enrollment and unenrollment handling.
- Step-by-step lesson completion with real-time percentage progress bars.
- Assessment quiz suite with multiple-choice questions, server-side scoring, instant pass/fail evaluation, and question explanations.
- **Quiz Security**: Answers are never exposed in HTML; scoring is atomic and server-side.

---

## 📁 Project Structure

```
SmartEdu/
├─ manage.py
├─ requirements.txt
├─ README.md
├─ config/                 # Project settings & URL routing
├─ accounts/               # Custom user model, auth, forms, profile
├─ core/                   # Public landing page, dashboards, static pages
├─ learning/               # LMS: Courses, Lessons, Resources, Quizzes, Progress
│  ├─ models.py
│  ├─ views.py
│  ├─ urls.py
│  ├─ forms.py
│  ├─ permissions.py
│  ├─ admin.py
│  └─ tests.py
├─ media/                  # Local media storage (thumbnails, resources)
├─ static/
│  ├─ css/style.css        # Premium SaaS stylesheet
│  └─ js/main.js
└─ templates/
   ├─ base.html
   ├─ includes/            # Navbar, footer, messages
   ├─ accounts/            # Register, profile
   ├─ registration/        # Login
   ├─ core/                # Home, dashboards, 403, 404
   └─ learning/            # Complete LMS template suite (19 templates)
```

---

## 📦 Media Storage & Production Architecture

### Local Development Storage:
- Files uploaded in development are saved to `BASE_DIR / 'media'` (`course_thumbnails/` and `course_resources/`).
- Handled securely via Django's `MEDIA_ROOT` and `download_resource` streaming response.

### Production Storage Considerations:
- In production, serving files directly from the web server disk can become a bottleneck and poses security limitations on multi-server or containerized deployments.
- Recommended production architecture:
  - Use cloud object storage (such as **Amazon S3**, **Google Cloud Storage**, or **Azure Blob Storage**) via `django-storages`.
  - For private course notes and PDF resources, generate short-lived signed URLs (presigned S3 URLs) inside the `download_resource` view instead of public direct S3 URLs.

---

## 💻 Commands for Windows PowerShell

```powershell
# 1. Activate Virtual Environment
.\.venv\Scripts\Activate.ps1

# 2. Run Database Migrations
python manage.py makemigrations
python manage.py migrate

# 3. Run Automated Test Suite
python manage.py test

# 4. Start Development Server
python manage.py runserver 127.0.0.1:8001
```

---

## 🧪 Testing

Run the comprehensive automated test suite:
```powershell
python manage.py test
```
All tests verify course ownership, student enrollment, lesson access controls, quiz scoring, is_correct isolation, and dashboard calculations.

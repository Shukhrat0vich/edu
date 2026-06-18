# 🎓 EduAnalytics — Student Performance Analytics Platform

A full-stack Django web application for analyzing educational data statistically and predicting student performance using Machine Learning.

---

## 🚀 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 4.2 + Django REST Framework |
| Database | PostgreSQL 15 |
| Frontend | Django Templates + Bootstrap 5 |
| Data Analysis | Pandas + NumPy |
| Machine Learning | scikit-learn (Linear Regression) |
| Charts | Chart.js |
| Authentication | JWT (SimpleJWT) |
| Deployment | Docker + Nginx + Gunicorn |

---

## ✨ Features

### 🔐 Authentication & Roles
- JWT-based authentication
- 3 user roles: **Admin**, **Teacher**, **Student**
- Role-based dashboards and access control
- Password hashing, CSRF protection

### 📊 Admin Dashboard
- Total students, average GPA, at-risk count
- Subject performance bar chart
- Top students ranking table
- Performance heatmap (Student × Subject)
- Attendance trends

### 👨‍🏫 Teacher Dashboard
- Subject averages with progress bars
- Student ranking for each subject
- Risk prediction overview

### 🎓 Student Dashboard
- Personal GPA and score breakdown
- Subject performance radar chart
- ML-powered final exam prediction
- Grade table with letter grades

### 📈 Analytics Module
- Descriptive statistics (mean, median, std dev, variance)
- Pearson correlation matrix
- Subject performance analysis
- Score distribution histogram
- Performance heatmap
- Top 10 students ranking
- Export to Excel and PDF

### 🤖 Machine Learning Module
- **Algorithm:** Linear Regression
- **Inputs:** Attendance %, Midterm score, Previous GPA
- **Output:** Predicted final exam score
- **Risk Detection:** Predicted final < 50 → "At Risk"
- Auto-trains on startup, saves model as `.pkl`
- Interactive prediction form with sliders

### 📡 REST API
```
POST   /api/login/              - Obtain JWT tokens
GET    /api/students/           - List students (admin/teacher)
GET    /api/analytics/summary/  - Statistical summary
GET    /api/analytics/correlation/ - Correlation matrix
GET    /api/ml/predict/         - Predict student performance
```

---

## ⚡ Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone the project
git clone <repo-url>
cd edu_analytics

# Start all services (DB, Redis, Django, Nginx)
docker-compose up --build

# The app starts at http://localhost
# Data is auto-seeded (1000 students) and ML model auto-trains
```

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env
# Edit .env with your database credentials

# 4. Create PostgreSQL database
createdb eduanalytics

# 5. Run migrations
python manage.py migrate

# 6. Generate fake data (1000 students)
python manage.py shell < scripts/generate_fake_data.py

# 7. Train ML model
python manage.py train_ml_model

# 8. Run development server
python manage.py runserver
```

---

## 🔑 Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@edu.com | admin123 |
| Teacher | teacher@edu.com | teacher123 |
| Student | student@edu.com | student123 |

---

## 📁 Project Structure

```
edu_analytics/
├── apps/
│   ├── users/              # Custom user model + auth
│   ├── academics/          # Student, Teacher, Subject, Grade, Attendance models
│   ├── analytics/          # Statistical analysis service + views
│   ├── ml_service/         # Linear Regression model service
│   ├── api/                # REST API endpoints
│   └── dashboard/          # Dashboard views
├── edu_analytics/
│   └── settings/
│       ├── base.py         # Shared settings
│       ├── dev.py          # Development
│       └── prod.py         # Production
├── templates/              # HTML templates
│   ├── base.html           # Main layout with sidebar
│   ├── users/              # Login, profile
│   ├── dashboard/          # Role dashboards + student detail
│   └── analytics/          # Analytics, correlation, heatmap
├── static/
│   ├── css/main.css        # Custom styles + dark mode
│   └── js/main.js          # Sidebar + dark mode toggle
├── scripts/
│   └── generate_fake_data.py
├── docker/
│   └── nginx.conf
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│              Presentation Layer (UI)                 │
│   Django Templates + Bootstrap 5 + Chart.js          │
└─────────────────────────┬───────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────┐
│              Business Logic Layer                    │
│   Analytics Service + ML Service + Serializers       │
└─────────────────────────┬───────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────┐
│                  Data Layer                          │
│   Django ORM + PostgreSQL + pandas DataFrames        │
└─────────────────────────────────────────────────────┘
```

---

## 📊 Database Models

```
User (Custom)          Student              Teacher
├── full_name          ├── user (1:1)       ├── user (1:1)
├── email              ├── faculty          ├── department
├── role               ├── group            └── experience_years
└── is_active          └── enrollment_year

Subject                Grade                Attendance
├── name               ├── student (FK)     ├── student (FK)
├── credit             ├── subject (FK)     ├── subject (FK)
└── teacher (FK)       ├── midterm          └── percentage
                       ├── final
                       ├── attendance
                       └── total_score (auto)
```

---

## 🤖 ML Model Details

- **Algorithm:** Linear Regression
- **Feature Engineering:**
  - `attendance_pct` — Attendance percentage (0–100)
  - `midterm_score` — Midterm exam score
  - `previous_gpa_scaled` — GPA × 25 (scaled to 0–100)
  - Interaction terms: `attendance × midterm`
- **Risk Thresholds:**
  - `≥ 70` → ✅ Safe
  - `50–70` → ⚡ Borderline
  - `< 50` → ⚠️ At Risk
- **Model file:** `ml_models/grade_predictor.pkl`
- Automatically reloads on server restart via `apps.py`

---

## 🔒 Security

- JWT authentication with access (60min) and refresh (7d) tokens
- Django password hashers (PBKDF2)
- CSRF protection on all forms
- Role-based permissions via custom permission classes
- SQL injection protection via Django ORM
- XSS protection via Django template escaping

---

## 📦 API Documentation

### POST /api/login/
```json
{
  "email": "admin@edu.com",
  "password": "admin123"
}
→ { "access": "...", "refresh": "...", "user": {...} }
```

### GET /api/students/
Headers: `Authorization: Bearer <token>`
Query params: `search`, `faculty`, `group`, `page`

### GET /api/analytics/summary/
Returns descriptive statistics, subject performance, top students.

### GET /api/analytics/correlation/
Returns Pearson correlation matrix for all grade metrics.

### POST /api/ml/predict/
```json
{ "attendance": 85, "midterm": 75, "previous_gpa": 3.2 }
→ { "predicted_final": 78.5, "risk_level": "safe", ... }
```

---

## 🎨 UI Features

- **Dark Mode** — Toggle via moon icon in sidebar
- **Responsive** — Mobile-first, works on all devices
- **Sidebar** — Collapsible with role-based nav items
- **Chart.js** — Bar, radar, scatter, pie charts
- **Pagination** — All list views paginated
- **Filtering & Search** — Students filterable by faculty, group, name

---

## 🚢 Production Deployment

```bash
# Set environment variables
export SECRET_KEY="your-production-secret-key"
export DEBUG=False
export ALLOWED_HOSTS="yourdomain.com"
export DATABASE_URL="postgresql://user:pass@host/db"

# Build and deploy
docker-compose -f docker-compose.yml up -d --build
```

---

## 📄 License

MIT License — Educational use welcome.

---

Built with ❤️ using Django, scikit-learn, and Chart.js
# edu

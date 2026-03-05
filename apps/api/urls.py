"""
REST API URL configuration.
All endpoints prefixed with /api/
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = 'api'

urlpatterns = [
    # ── Authentication ────────────────────────────────────────────────────────
    path('login/', views.LoginView.as_view(), name='login'),
    path('token/', views.LoginView.as_view(), name='token_obtain'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ── Students ──────────────────────────────────────────────────────────────
    path('students/', views.StudentListView.as_view(), name='student_list'),
    path('students/<int:pk>/', views.StudentDetailView.as_view(), name='student_detail'),

    # ── Teachers ──────────────────────────────────────────────────────────────
    path('teachers/', views.TeacherListView.as_view(), name='teacher_list'),

    # ── Subjects ──────────────────────────────────────────────────────────────
    path('subjects/', views.SubjectListView.as_view(), name='subject_list'),

    # ── Grades ────────────────────────────────────────────────────────────────
    path('grades/', views.GradeListCreateView.as_view(), name='grade_list'),

    # ── Analytics ─────────────────────────────────────────────────────────────
    path('analytics/summary/', views.AnalyticsSummaryView.as_view(), name='analytics_summary'),
    path('analytics/correlation/', views.CorrelationView.as_view(), name='analytics_correlation'),
    path('analytics/subjects/', views.SubjectPerformanceView.as_view(), name='analytics_subjects'),
    path('analytics/top-students/', views.TopStudentsView.as_view(), name='analytics_top_students'),
    path('analytics/at-risk/', views.AtRiskView.as_view(), name='analytics_at_risk'),

    # ── ML Prediction ─────────────────────────────────────────────────────────
    path('ml/predict/', views.PredictView.as_view(), name='ml_predict'),
    path('ml/model-info/', views.MLModelInfoView.as_view(), name='ml_model_info'),
]

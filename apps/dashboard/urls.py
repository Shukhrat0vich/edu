"""URL configuration for dashboard app."""
from django.urls import path
from . import views
from apps.ml_service.views import PredictionView

app_name = 'dashboard'

urlpatterns = [
    path('', views.HomeDashboardView.as_view(), name='home'),
    path('admin/', views.AdminDashboardView.as_view(), name='admin'),
    path('teacher/', views.TeacherDashboardView.as_view(), name='teacher'),
    path('student/', views.StudentDashboardView.as_view(), name='student'),
    path('students/', views.StudentListView.as_view(), name='student_list'),
    path('students/<int:pk>/', views.StudentDetailView.as_view(), name='student_detail'),
    path('predict/', PredictionView.as_view(), name='predict'),
    path('grades/add/', views.GradeCreateView.as_view(), name='grade_add'),
    path('grades/<int:pk>/edit/', views.GradeUpdateView.as_view(), name='grade_edit'),
    path('grades/<int:pk>/delete/', views.GradeDeleteView.as_view(), name='grade_delete'),
]

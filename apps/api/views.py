"""
REST API views for EduAnalytics.
Uses JWT authentication + role-based permissions.
"""
from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django_filters.rest_framework import DjangoFilterBackend

from apps.academics.models import Student, Teacher, Subject, Grade, Attendance
from apps.analytics.services import AnalyticsService
from apps.ml_service.ml_model import grade_predictor

from .serializers import (
    UserSerializer,
    StudentListSerializer,
    StudentDetailSerializer,
    TeacherSerializer,
    SubjectSerializer,
    GradeSerializer,
    GradeCreateSerializer,
    AttendanceSerializer,
    PredictionInputSerializer,
)
from .permissions import IsAdminOrTeacher, IsAdminOnly, IsOwnerOrAdmin


# ─── Custom JWT Token ─────────────────────────────────────────────────────────

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Add user info to JWT token response."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['full_name'] = user.full_name
        token['role'] = user.role
        token['email'] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'full_name': self.user.full_name,
            'email': self.user.email,
            'role': self.user.role,
        }
        return data


class LoginView(TokenObtainPairView):
    """POST /api/login — Returns JWT access + refresh tokens."""
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


# ─── Students ─────────────────────────────────────────────────────────────────

class StudentListView(generics.ListAPIView):
    """
    GET /api/students — List all students.
    Supports filtering by faculty, group, enrollment_year.
    Supports search by name/email.
    Paginated.
    """
    serializer_class = StudentListSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['faculty', 'group', 'enrollment_year']
    search_fields = ['user__full_name', 'user__email', 'group', 'faculty']
    ordering_fields = ['user__full_name', 'enrollment_year']
    ordering = ['user__full_name']

    def get_queryset(self):
        return Student.objects.select_related('user').all()


class StudentDetailView(generics.RetrieveAPIView):
    """GET /api/students/<id> — Student detail with grades."""
    serializer_class = StudentDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return Student.objects.all()
        elif user.role == 'TEACHER':
            return Student.objects.all()
        else:
            # Students can only see themselves
            return Student.objects.filter(user=user)


# ─── Teachers ─────────────────────────────────────────────────────────────────

class TeacherListView(generics.ListAPIView):
    """GET /api/teachers — List all teachers."""
    queryset = Teacher.objects.select_related('user').prefetch_related('subjects')
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated, IsAdminOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__full_name', 'department']
    ordering_fields = ['user__full_name', 'experience_years']


# ─── Subjects ─────────────────────────────────────────────────────────────────

class SubjectListView(generics.ListCreateAPIView):
    """GET/POST /api/subjects"""
    queryset = Subject.objects.select_related('teacher__user').all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'credit']


# ─── Grades ───────────────────────────────────────────────────────────────────

class GradeListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/grades"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['student', 'subject']
    ordering_fields = ['total_score', 'created_at']
    ordering = ['-total_score']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return Grade.objects.select_related('student__user', 'subject').all()
        elif user.role == 'TEACHER':
            return Grade.objects.filter(
                subject__teacher__user=user
            ).select_related('student__user', 'subject')
        else:
            try:
                student = user.student_profile
                return Grade.objects.filter(student=student).select_related('subject')
            except Exception:
                return Grade.objects.none()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return GradeCreateSerializer
        return GradeSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsAdminOrTeacher()]
        return [IsAuthenticated()]


# ─── Analytics ────────────────────────────────────────────────────────────────

class AnalyticsSummaryView(APIView):
    """GET /api/analytics/summary — Admin summary statistics."""
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]

    def get(self, request):
        summary = AnalyticsService.get_admin_summary()
        return Response(summary)


class CorrelationView(APIView):
    """GET /api/analytics/correlation — Pearson correlation matrix."""
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]

    def get(self, request):
        corr = AnalyticsService.get_correlation_matrix()
        return Response(corr)


class SubjectPerformanceView(APIView):
    """GET /api/analytics/subjects — Subject performance metrics."""
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]

    def get(self, request):
        data = AnalyticsService.get_subject_performance()
        return Response(data)


class TopStudentsView(APIView):
    """GET /api/analytics/top-students — Top student rankings."""
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]

    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        faculty = request.query_params.get('faculty')
        data = AnalyticsService.get_top_students(limit=limit, faculty=faculty)
        return Response(data)


class AtRiskView(APIView):
    """GET /api/analytics/at-risk — At-risk students."""
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]

    def get(self, request):
        data = AnalyticsService.get_at_risk_students()
        return Response(data)


# ─── ML Prediction ────────────────────────────────────────────────────────────

class PredictView(APIView):
    """
    POST /api/ml/predict

    Predicts final exam score based on:
    - attendance (float 0–100)
    - midterm (float 0–100)
    - previous_gpa (float 0–4.0, optional, default 2.5)

    Returns predicted final score and risk level.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PredictionInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not grade_predictor.is_ready():
            return Response(
                {'error': 'ML model not trained. Run: python manage.py train_ml_model'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        data = serializer.validated_data
        result = grade_predictor.predict(
            attendance=data['attendance'],
            midterm=data['midterm'],
            previous_gpa=data['previous_gpa'],
        )
        return Response(result, status=status.HTTP_200_OK)


class MLModelInfoView(APIView):
    """GET /api/ml/model-info — ML model metadata and metrics."""
    permission_classes = [IsAuthenticated, IsAdminOnly]

    def get(self, request):
        return Response(grade_predictor.get_model_info())

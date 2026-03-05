"""
DRF Serializers for EduAnalytics API.
"""
from rest_framework import serializers
from apps.users.models import User
from apps.academics.models import Student, Teacher, Subject, Grade, Attendance


# ─── User / Auth ──────────────────────────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'role', 'date_joined', 'is_active')
        read_only_fields = ('id', 'date_joined')


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'full_name', 'role', 'password', 'password_confirm')

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


# ─── Teacher ──────────────────────────────────────────────────────────────────

class TeacherSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    subject_count = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = ('id', 'full_name', 'email', 'department', 'experience_years', 'subject_count')

    def get_subject_count(self, obj):
        return obj.get_subject_count()


# ─── Student ──────────────────────────────────────────────────────────────────

class StudentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    gpa = serializers.SerializerMethodField()
    at_risk = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ('id', 'full_name', 'email', 'group', 'faculty', 'enrollment_year', 'gpa', 'at_risk')

    def get_gpa(self, obj):
        return obj.calculate_gpa()

    def get_at_risk(self, obj):
        return obj.is_at_risk()


class StudentDetailSerializer(StudentListSerializer):
    """Full serializer with nested grades."""
    grades = serializers.SerializerMethodField()

    class Meta(StudentListSerializer.Meta):
        fields = StudentListSerializer.Meta.fields + ('grades',)

    def get_grades(self, obj):
        grades = obj.grades.select_related('subject').all()
        return GradeSerializer(grades, many=True).data


# ─── Subject ──────────────────────────────────────────────────────────────────

class SubjectSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.user.full_name', read_only=True)
    avg_score = serializers.SerializerMethodField()
    pass_rate = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = ('id', 'name', 'credit', 'teacher', 'teacher_name', 'avg_score', 'pass_rate')

    def get_avg_score(self, obj):
        return round(obj.get_average_score(), 2)

    def get_pass_rate(self, obj):
        return obj.get_pass_rate()


# ─── Grade ────────────────────────────────────────────────────────────────────

class GradeSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    letter_grade = serializers.SerializerMethodField()

    class Meta:
        model = Grade
        fields = (
            'id', 'student', 'subject', 'subject_name',
            'midterm', 'final', 'attendance', 'total_score', 'letter_grade',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'total_score', 'created_at', 'updated_at')

    def get_letter_grade(self, obj):
        return obj.get_letter_grade()


class GradeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ('student', 'subject', 'midterm', 'final', 'attendance')

    def validate_midterm(self, value):
        if not 0 <= value <= 100:
            raise serializers.ValidationError('Midterm score must be between 0 and 100.')
        return value

    def validate_final(self, value):
        if not 0 <= value <= 100:
            raise serializers.ValidationError('Final score must be between 0 and 100.')
        return value

    def validate_attendance(self, value):
        if not 0 <= value <= 100:
            raise serializers.ValidationError('Attendance must be between 0 and 100.')
        return value


# ─── Attendance ───────────────────────────────────────────────────────────────

class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.full_name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)

    class Meta:
        model = Attendance
        fields = ('id', 'student', 'student_name', 'subject', 'subject_name', 'percentage', 'recorded_at')
        read_only_fields = ('id', 'recorded_at')


# ─── Analytics / ML ───────────────────────────────────────────────────────────

class PredictionInputSerializer(serializers.Serializer):
    attendance = serializers.FloatField(min_value=0, max_value=100)
    midterm = serializers.FloatField(min_value=0, max_value=100)
    previous_gpa = serializers.FloatField(min_value=0, max_value=4.0, default=2.5)


class AnalyticsSummarySerializer(serializers.Serializer):
    total_students = serializers.IntegerField()
    total_teachers = serializers.IntegerField()
    total_subjects = serializers.IntegerField()
    avg_gpa = serializers.FloatField()
    at_risk_count = serializers.IntegerField()
    avg_attendance = serializers.FloatField()

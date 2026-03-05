"""
Academic data models: Student, Teacher, Subject, Grade, Attendance.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
from apps.users.models import User


class Teacher(models.Model):
    """Teacher profile linked to User."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    department = models.CharField(max_length=100)
    experience_years = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'teachers'
        ordering = ['user__full_name']

    def __str__(self):
        return f'{self.user.full_name} — {self.department}'

    @property
    def full_name(self):
        return self.user.full_name

    @property
    def email(self):
        return self.user.email

    def get_subject_count(self):
        return self.subjects.count()

    def get_student_count(self):
        """Count distinct students across all subjects."""
        return Grade.objects.filter(subject__teacher=self).values('student').distinct().count()


class Student(models.Model):
    """Student profile linked to User."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    group = models.CharField(max_length=50)
    faculty = models.CharField(max_length=100)
    enrollment_year = models.PositiveSmallIntegerField()

    class Meta:
        db_table = 'students'
        ordering = ['user__full_name']

    def __str__(self):
        return f'{self.user.full_name} ({self.group})'

    @property
    def full_name(self):
        return self.user.full_name

    @property
    def email(self):
        return self.user.email

    def calculate_gpa(self):
        """Calculate GPA on a 0-4.0 scale based on total_score."""
        grades = self.grades.all()
        if not grades.exists():
            return 0.0
        avg = grades.aggregate(avg=Avg('total_score'))['avg'] or 0
        # Convert 0-100 score to 0-4.0 GPA
        return round(min(avg / 25, 4.0), 2)

    def is_at_risk(self):
        """Student is at risk if GPA < 2.0 or any final < 50."""
        gpa = self.calculate_gpa()
        if gpa < 2.0:
            return True
        return self.grades.filter(final__lt=50).exists()


class Subject(models.Model):
    """Academic subject taught by a teacher."""
    name = models.CharField(max_length=150)
    credit = models.PositiveSmallIntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(6)])
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='subjects')

    class Meta:
        db_table = 'subjects'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_average_score(self):
        return self.grades.aggregate(avg=Avg('total_score'))['avg'] or 0

    def get_pass_rate(self):
        total = self.grades.count()
        if not total:
            return 0
        passed = self.grades.filter(total_score__gte=50).count()
        return round(passed / total * 100, 1)


class Grade(models.Model):
    """
    Grade record for a student in a subject.
    total_score is auto-calculated: midterm*0.3 + final*0.5 + attendance*0.2
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grades')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='grades')
    midterm = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text='Midterm exam score (0–100)'
    )
    final = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text='Final exam score (0–100)'
    )
    attendance = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text='Attendance percentage (0–100)'
    )
    total_score = models.FloatField(editable=False, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'grades'
        unique_together = ('student', 'subject')
        ordering = ['-total_score']

    def __str__(self):
        return f'{self.student.full_name} — {self.subject.name}: {self.total_score:.1f}'

    def calculate_total_score(self):
        """Weighted formula: 30% midterm + 50% final + 20% attendance."""
        return round(self.midterm * 0.3 + self.final * 0.5 + self.attendance * 0.2, 2)

    def save(self, *args, **kwargs):
        """Auto-calculate total_score on save."""
        self.total_score = self.calculate_total_score()
        super().save(*args, **kwargs)

    def get_letter_grade(self):
        """Convert total_score to letter grade."""
        score = self.total_score
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'


class Attendance(models.Model):
    """Attendance record (aggregated by subject per student)."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='attendances')
    percentage = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text='Attendance percentage (0–100)'
    )
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'attendance'
        unique_together = ('student', 'subject')
        ordering = ['student', 'subject']

    def __str__(self):
        return f'{self.student.full_name} — {self.subject.name}: {self.percentage:.1f}%'

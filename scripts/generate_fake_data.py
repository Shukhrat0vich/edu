"""
EduAnalytics Fake Data Generator
==================================
Generates realistic academic data using normal distributions:
  - 1 Admin user
  - 20 Teachers (across departments)
  - 20 Subjects (assigned to teachers)
  - 1000 Students (across faculties/groups)
  - Grades for each student in 5-10 random subjects
  - Attendance records synced with grades

Usage:
  python manage.py shell < scripts/generate_fake_data.py
  OR
  python scripts/generate_fake_data.py  (if DJANGO_SETTINGS_MODULE is set)

Performance: ~3-5 minutes for 1000 students
"""
import os
import sys
import django
import random
import numpy as np
from datetime import datetime

# ── Django Setup ──────────────────────────────────────────────────────────────
if 'django' not in sys.modules or not django.conf.settings.configured:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edu_analytics.settings.dev')
    django.setup()

from django.db import transaction
from apps.users.models import User, UserRole
from apps.academics.models import Teacher, Student, Subject, Grade, Attendance

# ── Configuration ─────────────────────────────────────────────────────────────
NUM_STUDENTS = 1000
NUM_TEACHERS = 20
NUM_SUBJECTS = 20
SUBJECTS_PER_STUDENT = (5, 10)   # random range

FACULTIES = [
    'Computer Science',
    'Mathematics',
    'Physics',
    'Economics',
    'Engineering',
    'Business Administration',
    'Psychology',
    'Biology',
]

DEPARTMENTS = [
    'Computer Science', 'Mathematics', 'Physics',
    'Economics', 'Engineering', 'Business', 'Social Sciences', 'Natural Sciences',
]

SUBJECTS_LIST = [
    ('Calculus I', 4), ('Linear Algebra', 3), ('Statistics', 3),
    ('Database Systems', 3), ('Algorithms', 4), ('Operating Systems', 3),
    ('Web Development', 3), ('Machine Learning', 3), ('Data Structures', 4),
    ('Computer Networks', 3), ('Microeconomics', 3), ('Macroeconomics', 3),
    ('Financial Accounting', 3), ('Business Ethics', 2), ('Marketing', 3),
    ('General Physics', 4), ('Organic Chemistry', 3), ('Molecular Biology', 3),
    ('Research Methods', 2), ('Technical Writing', 2),
]

FIRST_NAMES = [
    'Alexander', 'Emma', 'James', 'Olivia', 'William', 'Ava', 'Benjamin', 'Sofia',
    'Lucas', 'Isabella', 'Mason', 'Mia', 'Ethan', 'Charlotte', 'Aiden', 'Amelia',
    'Noah', 'Harper', 'Liam', 'Evelyn', 'Michael', 'Abigail', 'Oliver', 'Emily',
    'Daniel', 'Elizabeth', 'Logan', 'Mila', 'Sebastian', 'Ella', 'Owen', 'Aria',
    'Samuel', 'Grace', 'Joseph', 'Chloe', 'Jack', 'Victoria', 'Henry', 'Riley',
    'Andrei', 'Fatima', 'Dmitri', 'Aisha', 'Kenji', 'Yuki', 'Carlos', 'Maria',
    'Arjun', 'Priya', 'Ahmed', 'Zara', 'Ivan', 'Natasha', 'Marco', 'Sofia',
    'Kwame', 'Amara', 'Sven', 'Ingrid', 'Ravi', 'Lakshmi', 'Omar', 'Leila',
]

LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
    'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
    'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
    'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson',
    'Ivanov', 'Petrov', 'Sidorov', 'Karimov', 'Tanaka', 'Yamamoto', 'Kim', 'Park',
    'Singh', 'Kumar', 'Patel', 'Shah', 'Ahmed', 'Hassan', 'Ali', 'Khan',
    'Mueller', 'Schmidt', 'Fischer', 'Weber', 'Dupont', 'Bernard', 'Moreau',
]

def random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def generate_grade(performance_level=None):
    """
    Generate realistic grades using normal distribution.
    performance_level: None=average, 'high'=top students, 'low'=struggling students
    """
    if performance_level == 'high':
        mean_midterm, std_midterm = 82, 8
        mean_final, std_final = 85, 7
        mean_attendance = 90
    elif performance_level == 'low':
        mean_midterm, std_midterm = 42, 12
        mean_final, std_final = 38, 14
        mean_attendance = 55
    else:
        mean_midterm, std_midterm = 65, 15
        mean_final, std_final = 62, 18
        mean_attendance = 75

    midterm = float(np.clip(np.random.normal(mean_midterm, std_midterm), 0, 100))
    final = float(np.clip(np.random.normal(mean_final, std_final), 0, 100))
    attendance = float(np.clip(np.random.normal(mean_attendance, 12), 0, 100))

    return round(midterm, 1), round(final, 1), round(attendance, 1)


def print_progress(current, total, label='Progress'):
    percent = int(current / total * 100)
    bar = '█' * (percent // 5) + '░' * (20 - percent // 5)
    print(f'\r  {label}: [{bar}] {percent}% ({current}/{total})', end='', flush=True)


@transaction.atomic
def generate_data():
    print('🚀 EduAnalytics Data Generator')
    print('=' * 50)

    # ── Clean existing data ────────────────────────────────────────────────────
    print('\n📦 Clearing existing data...')
    Attendance.objects.all().delete()
    Grade.objects.all().delete()
    Subject.objects.all().delete()
    Student.objects.all().delete()
    Teacher.objects.all().delete()
    User.objects.filter(role__in=[UserRole.STUDENT, UserRole.TEACHER]).delete()
    print('   ✅ Done')

    # ── Admin user ─────────────────────────────────────────────────────────────
    print('\n👑 Creating admin user...')
    admin, created = User.objects.get_or_create(
        email='admin@edu.com',
        defaults={
            'full_name': 'System Administrator',
            'role': UserRole.ADMIN,
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if created:
        admin.set_password('admin123')
        admin.save()
    print(f'   ✅ Admin: admin@edu.com / admin123')

    # ── Demo Teacher ───────────────────────────────────────────────────────────
    demo_teacher_user, _ = User.objects.get_or_create(
        email='teacher@edu.com',
        defaults={'full_name': 'Demo Teacher', 'role': UserRole.TEACHER}
    )
    demo_teacher_user.set_password('teacher123')
    demo_teacher_user.save()

    # ── Demo Student ───────────────────────────────────────────────────────────
    demo_student_user, _ = User.objects.get_or_create(
        email='student@edu.com',
        defaults={'full_name': 'Demo Student', 'role': UserRole.STUDENT}
    )
    demo_student_user.set_password('student123')
    demo_student_user.save()

    # ── Teachers ───────────────────────────────────────────────────────────────
    print(f'\n👨‍🏫 Creating {NUM_TEACHERS} teachers...')
    teachers = []
    emails_used = {'admin@edu.com', 'teacher@edu.com', 'student@edu.com'}

    for i in range(NUM_TEACHERS):
        name = random_name()
        email = f"teacher.{i+1}@edu.com"

        user = User.objects.create_user(
            email=email,
            full_name=name,
            password='teacher123',
            role=UserRole.TEACHER,
        )
        teacher = Teacher.objects.create(
            user=user,
            department=random.choice(DEPARTMENTS),
            experience_years=random.randint(1, 30),
        )
        teachers.append(teacher)
        print_progress(i + 1, NUM_TEACHERS, 'Teachers')

    # Attach demo teacher
    if not hasattr(demo_teacher_user, 'teacher_profile'):
        demo_teacher = Teacher.objects.create(
            user=demo_teacher_user,
            department='Computer Science',
            experience_years=5,
        )
    else:
        demo_teacher = demo_teacher_user.teacher_profile
    teachers.insert(0, demo_teacher)
    print(f'\n   ✅ Created {len(teachers)} teachers')

    # ── Subjects ───────────────────────────────────────────────────────────────
    print(f'\n📚 Creating {NUM_SUBJECTS} subjects...')
    subjects = []
    for i, (name, credit) in enumerate(SUBJECTS_LIST):
        teacher = teachers[i % len(teachers)]
        subject = Subject.objects.create(
            name=name,
            credit=credit,
            teacher=teacher,
        )
        subjects.append(subject)
    print(f'   ✅ Created {len(subjects)} subjects')

    # ── Students ───────────────────────────────────────────────────────────────
    print(f'\n🎓 Creating {NUM_STUDENTS} students with grades...')

    # Performance distribution:
    # 20% high performers, 60% average, 20% struggling
    performance_levels = (
        ['high'] * int(NUM_STUDENTS * 0.20) +
        [None] * int(NUM_STUDENTS * 0.60) +
        ['low'] * int(NUM_STUDENTS * 0.20)
    )
    random.shuffle(performance_levels)

    student_objects = []
    grade_objects = []
    attendance_objects = []

    for i in range(NUM_STUDENTS):
        faculty = random.choice(FACULTIES)
        group_num = random.randint(1, 5)
        group = f"{faculty[:2].upper()}-{random.choice(['21','22','23','24'])}-{group_num:02d}"
        enrollment_year = random.randint(2019, 2023)
        name = random_name()
        email = f"student.{i+1}@edu.com"

        user = User.objects.create_user(
            email=email,
            full_name=name,
            password='student123',
            role=UserRole.STUDENT,
        )
        student = Student.objects.create(
            user=user,
            group=group,
            faculty=faculty,
            enrollment_year=enrollment_year,
        )
        student_objects.append(student)

        # Assign random subjects
        num_subjects = random.randint(*SUBJECTS_PER_STUDENT)
        student_subjects = random.sample(subjects, min(num_subjects, len(subjects)))
        perf = performance_levels[i]

        for subject in student_subjects:
            midterm, final, attendance = generate_grade(perf)

            # Grade (auto-calculates total_score)
            grade = Grade(
                student=student,
                subject=subject,
                midterm=midterm,
                final=final,
                attendance=attendance,
            )
            grade.total_score = grade.calculate_total_score()
            grade_objects.append(grade)

            # Attendance record
            attendance_objects.append(Attendance(
                student=student,
                subject=subject,
                percentage=attendance,
            ))

        print_progress(i + 1, NUM_STUDENTS, 'Students')

    # Bulk create for performance
    print(f'\n   💾 Saving {len(grade_objects)} grade records...')
    Grade.objects.bulk_create(grade_objects, batch_size=500)
    print(f'   💾 Saving {len(attendance_objects)} attendance records...')
    Attendance.objects.bulk_create(attendance_objects, batch_size=500, ignore_conflicts=True)

    # Attach demo student
    if not hasattr(demo_student_user, 'student_profile'):
        demo_student = Student.objects.create(
            user=demo_student_user,
            group='CS-23-01',
            faculty='Computer Science',
            enrollment_year=2023,
        )
        # Give demo student grades in first 8 subjects
        for subject in subjects[:8]:
            midterm, final, att = generate_grade()
            grade = Grade.objects.create(
                student=demo_student,
                subject=subject,
                midterm=midterm,
                final=final,
                attendance=att,
            )
            Attendance.objects.get_or_create(
                student=demo_student,
                subject=subject,
                defaults={'percentage': att},
            )

    print(f'\n   ✅ Created {len(student_objects)} students')

    # ── Summary ────────────────────────────────────────────────────────────────
    print('\n' + '=' * 50)
    print('✅ Data generation complete!')
    print(f'   👑 Admins:    {User.objects.filter(role=UserRole.ADMIN).count()}')
    print(f'   👨‍🏫 Teachers:  {User.objects.filter(role=UserRole.TEACHER).count()}')
    print(f'   🎓 Students:  {User.objects.filter(role=UserRole.STUDENT).count()}')
    print(f'   📚 Subjects:  {Subject.objects.count()}')
    print(f'   📊 Grades:    {Grade.objects.count()}')
    print(f'   📅 Attendance:{Attendance.objects.count()}')
    print()
    print('🔑 Demo Credentials:')
    print('   Admin:   admin@edu.com    / admin123')
    print('   Teacher: teacher@edu.com  / teacher123')
    print('   Student: student@edu.com  / student123')
    print()
    print('🤖 Next: Train the ML model:')
    print('   python manage.py train_ml_model')


if __name__ == '__main__':
    generate_data()

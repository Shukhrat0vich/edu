"""
Statistical Analysis Service using Pandas & NumPy.
Provides mean, median, std dev, variance, correlation matrix,
top student rankings, and subject performance analysis.
"""
import numpy as np
import pandas as pd
from django.db.models import Avg, Count, Max, Min, StdDev
from apps.academics.models import Grade, Student, Subject, Attendance


class AnalyticsService:
    """
    Service layer for all statistical analysis.
    Separates business logic from views.
    """

    # ──────────────────────────────────────────────────────────────────────────
    #  Core statistics
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_grades_dataframe(subject_id=None, faculty=None):
        """Return a pandas DataFrame with all grade data."""
        qs = Grade.objects.select_related('student__user', 'subject', 'subject__teacher__user')

        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        if faculty:
            qs = qs.filter(student__faculty=faculty)

        records = list(qs.values(
            'student_id',
            'student__user__full_name',
            'student__faculty',
            'student__group',
            'subject__name',
            'midterm',
            'final',
            'attendance',
            'total_score',
        ))

        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)
        df.rename(columns={
            'student__user__full_name': 'student_name',
            'student__faculty': 'faculty',
            'student__group': 'group',
            'subject__name': 'subject_name',
        }, inplace=True)
        return df

    @staticmethod
    def compute_descriptive_stats(df=None, column='total_score'):
        """
        Compute descriptive statistics for a numeric column.
        Returns a dict with mean, median, std, variance, min, max, count.
        """
        if df is None:
            df = AnalyticsService.get_grades_dataframe()

        if df.empty or column not in df.columns:
            return {}

        series = df[column].dropna()

        return {
            'mean': round(float(series.mean()), 2),
            'median': round(float(series.median()), 2),
            'std': round(float(series.std()), 2),
            'variance': round(float(series.var()), 2),
            'min': round(float(series.min()), 2),
            'max': round(float(series.max()), 2),
            'count': int(series.count()),
            'q1': round(float(series.quantile(0.25)), 2),
            'q3': round(float(series.quantile(0.75)), 2),
        }

    @staticmethod
    def get_correlation_matrix():
        """
        Compute Pearson correlation matrix for numeric grade columns.
        Returns: dict {column: {column: value}}
        """
        df = AnalyticsService.get_grades_dataframe()
        if df.empty:
            return {}

        numeric_cols = ['midterm', 'final', 'attendance', 'total_score']
        available = [c for c in numeric_cols if c in df.columns]
        corr_df = df[available].corr(method='pearson').round(3)
        return corr_df.to_dict()

    # ──────────────────────────────────────────────────────────────────────────
    #  Rankings
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_top_students(limit=10, faculty=None):
        """
        Return top students ranked by average total_score.
        Returns a list of dicts with student info and avg score.
        """
        qs = Grade.objects.select_related('student__user')
        if faculty:
            qs = qs.filter(student__faculty=faculty)

        ranking = (
            qs
            .values('student_id', 'student__user__full_name', 'student__faculty', 'student__group')
            .annotate(avg_score=Avg('total_score'), subject_count=Count('subject'))
            .order_by('-avg_score')[:limit]
        )

        result = []
        for i, row in enumerate(ranking, 1):
            result.append({
                'rank': i,
                'student_id': row['student_id'],
                'full_name': row['student__user__full_name'],
                'faculty': row['student__faculty'],
                'group': row['student__group'],
                'avg_score': round(row['avg_score'], 2),
                'gpa': round(min(row['avg_score'] / 25, 4.0), 2),
                'subject_count': row['subject_count'],
            })
        return result

    @staticmethod
    def get_at_risk_students():
        """Return students with average total_score < 50 (at risk of failing)."""
        at_risk = (
            Grade.objects
            .values('student_id', 'student__user__full_name', 'student__faculty', 'student__group')
            .annotate(avg_score=Avg('total_score'), fail_count=Count('id'))
            .filter(avg_score__lt=50)
            .order_by('avg_score')
        )

        return [
            {
                'student_id': row['student_id'],
                'full_name': row['student__user__full_name'],
                'faculty': row['student__faculty'],
                'group': row['student__group'],
                'avg_score': round(row['avg_score'], 2),
                'gpa': round(min(row['avg_score'] / 25, 4.0), 2),
            }
            for row in at_risk
        ]

    # ──────────────────────────────────────────────────────────────────────────
    #  Subject Analysis
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_subject_performance():
        """
        Return performance metrics for every subject.
        Returns a list of dicts sorted by avg_score descending.
        """
        subjects = Subject.objects.prefetch_related('grades')
        result = []

        for subject in subjects:
            grades_qs = subject.grades.all()
            if not grades_qs.exists():
                continue

            stats = grades_qs.aggregate(
                avg_score=Avg('total_score'),
                max_score=Max('total_score'),
                min_score=Min('total_score'),
                std_score=StdDev('total_score'),
                total_students=Count('id'),
            )
            pass_count = grades_qs.filter(total_score__gte=50).count()

            result.append({
                'subject_id': subject.id,
                'subject_name': subject.name,
                'credit': subject.credit,
                'teacher': subject.teacher.full_name if subject.teacher else 'N/A',
                'avg_score': round(stats['avg_score'] or 0, 2),
                'max_score': round(stats['max_score'] or 0, 2),
                'min_score': round(stats['min_score'] or 0, 2),
                'std_score': round(stats['std_score'] or 0, 2),
                'total_students': stats['total_students'],
                'pass_rate': round(pass_count / stats['total_students'] * 100, 1) if stats['total_students'] else 0,
            })

        return sorted(result, key=lambda x: x['avg_score'], reverse=True)

    # ──────────────────────────────────────────────────────────────────────────
    #  Dashboard summary stats
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_admin_summary():
        """
        Return summary statistics for admin dashboard.
        """
        from apps.academics.models import Teacher
        total_students = Student.objects.count()
        total_teachers = Teacher.objects.count()
        total_subjects = Subject.objects.count()
        total_grades = Grade.objects.count()

        avg_gpa_data = Grade.objects.aggregate(avg=Avg('total_score'))
        avg_score = avg_gpa_data['avg'] or 0
        avg_gpa = round(min(avg_score / 25, 4.0), 2)

        at_risk_count = len(AnalyticsService.get_at_risk_students())

        # Grade distribution
        grade_dist = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
        for grade in Grade.objects.only('total_score'):
            letter = _score_to_letter(grade.total_score)
            grade_dist[letter] = grade_dist.get(letter, 0) + 1

        # Attendance average
        att_avg = Attendance.objects.aggregate(avg=Avg('percentage'))['avg'] or 0

        return {
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_subjects': total_subjects,
            'total_grades': total_grades,
            'avg_gpa': avg_gpa,
            'avg_score': round(avg_score, 2),
            'at_risk_count': at_risk_count,
            'grade_distribution': grade_dist,
            'avg_attendance': round(att_avg, 1),
        }

    @staticmethod
    def get_teacher_summary(teacher):
        """Summary stats for a specific teacher."""
        subjects = teacher.subjects.all()
        subject_ids = subjects.values_list('id', flat=True)
        grades_qs = Grade.objects.filter(subject_id__in=subject_ids)

        avg_score = grades_qs.aggregate(avg=Avg('total_score'))['avg'] or 0
        student_count = grades_qs.values('student').distinct().count()
        at_risk = grades_qs.values('student').annotate(avg=Avg('total_score')).filter(avg__lt=50).count()

        subject_data = []
        for subject in subjects:
            s_grades = subject.grades.all()
            avg = s_grades.aggregate(avg=Avg('total_score'))['avg'] or 0
            subject_data.append({
                'name': subject.name,
                'avg_score': round(avg, 2),
                'student_count': s_grades.count(),
            })

        return {
            'subject_count': subjects.count(),
            'student_count': student_count,
            'avg_score': round(avg_score, 2),
            'at_risk_count': at_risk,
            'subjects': subject_data,
        }

    @staticmethod
    def get_student_summary(student):
        """Summary stats for a specific student."""
        grades = student.grades.select_related('subject').all()
        gpa = student.calculate_gpa()
        at_risk = student.is_at_risk()

        subject_scores = [
            {
                'subject': g.subject.name,
                'midterm': g.midterm,
                'final': g.final,
                'attendance': g.attendance,
                'total_score': g.total_score,
                'letter': g.get_letter_grade(),
            }
            for g in grades
        ]

        scores = [g.total_score for g in grades]
        return {
            'gpa': gpa,
            'avg_score': round(np.mean(scores), 2) if scores else 0,
            'best_score': round(max(scores), 2) if scores else 0,
            'worst_score': round(min(scores), 2) if scores else 0,
            'at_risk': at_risk,
            'subject_count': len(subject_scores),
            'subjects': subject_scores,
        }

    # ──────────────────────────────────────────────────────────────────────────
    #  Heatmap data (for admin analytics)
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_heatmap_data(top_n_subjects=10, top_n_students=20):
        """
        Build heatmap matrix: students × subjects with total_score values.
        Returns: labels (students, subjects) + matrix data for Chart.js.
        """
        subjects = Subject.objects.order_by('-grades__total_score').distinct()[:top_n_subjects]
        top_students_ids = (
            Grade.objects
            .values('student_id')
            .annotate(avg=Avg('total_score'))
            .order_by('-avg')[:top_n_students]
        )
        student_ids = [row['student_id'] for row in top_students_ids]
        students = Student.objects.filter(id__in=student_ids).select_related('user')

        subject_names = [s.name for s in subjects]
        student_names = [s.full_name for s in students]

        # Build matrix
        grade_map = {}
        for g in Grade.objects.filter(student__in=students, subject__in=subjects):
            grade_map[(g.student_id, g.subject_id)] = g.total_score

        matrix = []
        for student in students:
            row = []
            for subject in subjects:
                score = grade_map.get((student.id, subject.id), None)
                row.append(round(score, 1) if score is not None else None)
            matrix.append(row)

        return {
            'students': student_names,
            'subjects': subject_names,
            'matrix': matrix,
        }

    @staticmethod
    def get_attendance_trends():
        """Return attendance percentage by faculty for trend charts."""
        data = (
            Attendance.objects
            .values('student__faculty')
            .annotate(avg_attendance=Avg('percentage'))
            .order_by('student__faculty')
        )
        return [
            {'faculty': row['student__faculty'], 'avg_attendance': round(row['avg_attendance'], 1)}
            for row in data
        ]

    @staticmethod
    def get_score_distribution():
        """Return score distribution bins for histogram."""
        scores = list(Grade.objects.values_list('total_score', flat=True))
        if not scores:
            return []
        arr = np.array(scores)
        counts, bin_edges = np.histogram(arr, bins=10, range=(0, 100))
        return [
            {
                'range': f'{int(bin_edges[i])}–{int(bin_edges[i+1])}',
                'count': int(counts[i]),
            }
            for i in range(len(counts))
        ]


def _score_to_letter(score):
    """Convert numeric score to letter grade."""
    if score >= 90:
        return 'A'
    elif score >= 80:
        return 'B'
    elif score >= 70:
        return 'C'
    elif score >= 60:
        return 'D'
    return 'F'

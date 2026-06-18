"""
Dashboard views for Admin, Teacher, and Student roles.
Uses service layer to separate business logic from views.
"""
import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count as DjCount
from django.contrib import messages

from apps.users.models import UserRole
from apps.academics.models import Student, Teacher, Subject, Grade, Attendance
from apps.analytics.services import AnalyticsService
from apps.ml_service.ml_model import grade_predictor


def role_redirect(request):
    """Redirect user to appropriate dashboard based on role."""
    if not request.user.is_authenticated:
        return redirect('users:login')
    role = request.user.role
    if role == UserRole.ADMIN:
        return redirect('dashboard:admin')
    elif role == UserRole.TEACHER:
        return redirect('dashboard:teacher')
    else:
        return redirect('dashboard:student')


@method_decorator(login_required, name='dispatch')
class HomeDashboardView(View):
    """Redirects to the role-appropriate dashboard."""

    def get(self, request):
        return role_redirect(request)


# ─── Admin Dashboard ──────────────────────────────────────────────────────────

@method_decorator(login_required, name='dispatch')
class AdminDashboardView(View):
    """Admin dashboard with system-wide statistics."""
    template_name = 'dashboard/admin.html'

    def get(self, request):
        if request.user.role != UserRole.ADMIN:
            return redirect('dashboard:home')

        summary = AnalyticsService.get_admin_summary()
        top_students = AnalyticsService.get_top_students(limit=5)
        at_risk = AnalyticsService.get_at_risk_students()[:5]
        all_at_risk = AnalyticsService.get_at_risk_students()
        all_students = AnalyticsService.get_top_students(limit=1000)
        subject_perf = AnalyticsService.get_subject_performance()[:8]
        all_subjects = AnalyticsService.get_subject_performance()
        attendance_trends = AnalyticsService.get_attendance_trends()
        score_dist = AnalyticsService.get_score_distribution()

        teachers = Teacher.objects.select_related('user').annotate(
            subject_count=DjCount('subjects')
        ).all()
        teachers_data = [{
            'name': t.user.full_name,
            'department': t.department,
            'experience': t.experience_years,
            'subjects': t.subject_count,
        } for t in teachers]

        # Grade management data for admin
        all_students_qs = Student.objects.select_related('user').order_by('user__full_name')
        subjects_with_grades = []
        for subj in Subject.objects.select_related('teacher__user').order_by('name'):
            grades = Grade.objects.filter(subject=subj).select_related('student__user').order_by('-total_score')
            graded_ids = set(grades.values_list('student_id', flat=True))
            ungraded = [s for s in all_students_qs if s.pk not in graded_ids]
            subjects_with_grades.append({
                'subject': subj,
                'grades': grades,
                'avg_score': subj.get_average_score(),
                'pass_rate': subj.get_pass_rate(),
                'ungraded_students': ungraded,
            })

        context = {
            'summary': summary,
            'top_students': top_students,
            'at_risk': at_risk,
            'subject_performance': subject_perf,
            'subject_perf_json': json.dumps(subject_perf),
            'attendance_trends_json': json.dumps(attendance_trends),
            'score_dist_json': json.dumps(score_dist),
            'grade_dist_json': json.dumps(summary.get('grade_distribution', {})),
            'all_at_risk_json': json.dumps(all_at_risk),
            'all_students_json': json.dumps(all_students),
            'all_subjects_json': json.dumps(all_subjects),
            'teachers_json': json.dumps(teachers_data),
            'subjects_with_grades': subjects_with_grades,
        }
        return render(request, self.template_name, context)


# ─── Teacher Dashboard ────────────────────────────────────────────────────────

@method_decorator(login_required, name='dispatch')
class TeacherDashboardView(View):
    """Teacher dashboard with subject-specific data."""
    template_name = 'dashboard/teacher.html'

    def get(self, request):
        if request.user.role != UserRole.TEACHER:
            return redirect('dashboard:home')

        try:
            teacher = request.user.teacher_profile
        except Teacher.DoesNotExist:
            return render(request, 'dashboard/no_profile.html', {'role': 'teacher'})

        summary = AnalyticsService.get_teacher_summary(teacher)

        # Subject-specific data with all students per subject
        all_students_qs = Student.objects.select_related('user').order_by('user__full_name')
        subject_data = []
        for subject in teacher.subjects.all():
            grades = Grade.objects.filter(subject=subject).select_related('student__user').order_by('-total_score')
            graded_student_ids = set(grades.values_list('student_id', flat=True))
            ungraded_students = [s for s in all_students_qs if s.pk not in graded_student_ids]
            subject_data.append({
                'subject': subject,
                'top_students': grades,
                'avg_score': subject.get_average_score(),
                'pass_rate': subject.get_pass_rate(),
                'ungraded_students': ungraded_students,
            })

        # At-risk students for this teacher's subjects
        subject_ids = teacher.subjects.values_list('id', flat=True)
        at_risk_grades = (
            Grade.objects
            .filter(subject_id__in=subject_ids, total_score__lt=50)
            .select_related('student__user', 'subject')
            .order_by('total_score')[:10]
        )

        context = {
            'teacher': teacher,
            'summary': summary,
            'subject_data': subject_data,
            'at_risk_grades': at_risk_grades,
            'subjects_json': json.dumps(summary.get('subjects', [])),
        }
        return render(request, self.template_name, context)


# ─── Student Dashboard ────────────────────────────────────────────────────────

@method_decorator(login_required, name='dispatch')
class StudentDashboardView(View):
    """Student personal dashboard."""
    template_name = 'dashboard/student.html'

    def get(self, request):
        if request.user.role != UserRole.STUDENT:
            return redirect('dashboard:home')

        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return render(request, 'dashboard/no_profile.html', {'role': 'student'})

        summary = AnalyticsService.get_student_summary(student)

        # ML Prediction (using average attendance and midterm)
        prediction = None
        if grade_predictor.is_ready() and summary['subjects']:
            import numpy as np
            scores = summary['subjects']
            avg_att = float(np.mean([s['attendance'] for s in scores]))
            avg_mid = float(np.mean([s['midterm'] for s in scores]))
            gpa = summary['gpa']
            try:
                prediction = grade_predictor.predict(avg_att, avg_mid, gpa)
            except Exception:
                pass

        context = {
            'student': student,
            'summary': summary,
            'prediction': prediction,
            'subjects_json': json.dumps(summary.get('subjects', [])),
        }
        return render(request, self.template_name, context)


# ─── Student List (Admin/Teacher) ─────────────────────────────────────────────

@method_decorator(login_required, name='dispatch')
class StudentListView(View):
    """Paginated, searchable student list for admin/teacher."""
    template_name = 'dashboard/students.html'

    def get(self, request):
        if request.user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
            return redirect('dashboard:home')

        search = request.GET.get('search', '').strip()
        faculty = request.GET.get('faculty', '')
        group = request.GET.get('group', '')

        qs = Student.objects.select_related('user').all()

        if search:
            qs = qs.filter(
                Q(user__full_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(group__icontains=search)
            )
        if faculty:
            qs = qs.filter(faculty=faculty)
        if group:
            qs = qs.filter(group=group)

        paginator = Paginator(qs, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        faculties = Student.objects.values_list('faculty', flat=True).distinct().order_by('faculty')
        groups = Student.objects.values_list('group', flat=True).distinct().order_by('group')

        context = {
            'page_obj': page_obj,
            'search': search,
            'faculty': faculty,
            'group': group,
            'faculties': faculties,
            'groups': groups,
            'total_count': qs.count(),
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class StudentDetailView(View):
    """Individual student detail page."""
    template_name = 'dashboard/student_detail.html'

    def get(self, request, pk):
        if request.user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
            if request.user.role == UserRole.STUDENT:
                try:
                    if request.user.student_profile.pk != pk:
                        return HttpResponse('403 Forbidden', status=403)
                except Exception:
                    return HttpResponse('403 Forbidden', status=403)

        student = get_object_or_404(Student.objects.select_related('user'), pk=pk)
        summary = AnalyticsService.get_student_summary(student)

        # ML prediction
        prediction = None
        if grade_predictor.is_ready() and summary['subjects']:
            import numpy as np
            scores = summary['subjects']
            avg_att = float(np.mean([s['attendance'] for s in scores]))
            avg_mid = float(np.mean([s['midterm'] for s in scores]))
            try:
                prediction = grade_predictor.predict(avg_att, avg_mid, summary['gpa'])
            except Exception:
                pass

        context = {
            'student': student,
            'summary': summary,
            'prediction': prediction,
            'subjects_json': json.dumps(summary.get('subjects', [])),
        }
        return render(request, self.template_name, context)


# ─── Grade Management (Admin & Teacher) ──────────────────────────────────────

def _grade_redirect(request):
    """Redirect back to the appropriate dashboard after a grade action."""
    if request.user.role == UserRole.ADMIN:
        return redirect('dashboard:admin')
    return redirect('dashboard:teacher')


@method_decorator(login_required, name='dispatch')
class GradeCreateView(View):
    """
    Create a grade for a student in a subject.
    Admin: any subject. Teacher: only their own subjects.
    """

    def post(self, request):
        role = request.user.role
        if role not in (UserRole.ADMIN, UserRole.TEACHER):
            return JsonResponse({'error': 'Forbidden'}, status=403)

        subject_id = request.POST.get('subject_id')
        student_id = request.POST.get('student_id')
        midterm = request.POST.get('midterm')
        final_score = request.POST.get('final')
        attendance = request.POST.get('attendance')

        if role == UserRole.TEACHER:
            try:
                teacher = request.user.teacher_profile
            except Teacher.DoesNotExist:
                return JsonResponse({'error': 'No teacher profile'}, status=403)
            subject = get_object_or_404(Subject, pk=subject_id, teacher=teacher)
        else:
            subject = get_object_or_404(Subject, pk=subject_id)

        student = get_object_or_404(Student, pk=student_id)

        if Grade.objects.filter(student=student, subject=subject).exists():
            messages.error(request, f'Grade already exists for {student.full_name} in {subject.name}.')
            return _grade_redirect(request)

        try:
            grade = Grade(
                student=student,
                subject=subject,
                midterm=float(midterm),
                final=float(final_score),
                attendance=float(attendance),
            )
            grade.full_clean()
            grade.save()
            messages.success(request, f'Grade added for {student.full_name} in {subject.name}.')
        except Exception as e:
            messages.error(request, f'Error: {e}')

        return _grade_redirect(request)


@method_decorator(login_required, name='dispatch')
class GradeUpdateView(View):
    """
    Update an existing grade.
    Admin: any grade. Teacher: only grades in their subjects.
    """

    def post(self, request, pk):
        role = request.user.role
        if role not in (UserRole.ADMIN, UserRole.TEACHER):
            return JsonResponse({'error': 'Forbidden'}, status=403)

        if role == UserRole.TEACHER:
            try:
                teacher = request.user.teacher_profile
            except Teacher.DoesNotExist:
                return JsonResponse({'error': 'No teacher profile'}, status=403)
            grade = get_object_or_404(Grade, pk=pk, subject__teacher=teacher)
        else:
            grade = get_object_or_404(Grade, pk=pk)

        try:
            grade.midterm = float(request.POST.get('midterm', grade.midterm))
            grade.final = float(request.POST.get('final', grade.final))
            grade.attendance = float(request.POST.get('attendance', grade.attendance))
            grade.full_clean()
            grade.save()
            messages.success(request, f'Grade updated for {grade.student.full_name}.')
        except Exception as e:
            messages.error(request, f'Error: {e}')

        return _grade_redirect(request)


@method_decorator(login_required, name='dispatch')
class GradeDeleteView(View):
    """
    Delete a grade.
    Admin: any grade. Teacher: only grades in their subjects.
    """

    def post(self, request, pk):
        role = request.user.role
        if role not in (UserRole.ADMIN, UserRole.TEACHER):
            return JsonResponse({'error': 'Forbidden'}, status=403)

        if role == UserRole.TEACHER:
            try:
                teacher = request.user.teacher_profile
            except Teacher.DoesNotExist:
                return JsonResponse({'error': 'No teacher profile'}, status=403)
            grade = get_object_or_404(Grade, pk=pk, subject__teacher=teacher)
        else:
            grade = get_object_or_404(Grade, pk=pk)

        name = grade.student.full_name
        subject_name = grade.subject.name
        grade.delete()
        messages.success(request, f'Grade deleted for {name} in {subject_name}.')
        return _grade_redirect(request)

"""Admin configuration for Academics app."""
from django.contrib import admin
from .models import Teacher, Student, Subject, Grade, Attendance


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'department', 'experience_years', 'get_subject_count')
    list_filter = ('department',)
    search_fields = ('user__full_name', 'user__email', 'department')

    def get_subject_count(self, obj):
        return obj.get_subject_count()
    get_subject_count.short_description = 'Subjects'


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'group', 'faculty', 'enrollment_year', 'calculate_gpa', 'is_at_risk')
    list_filter = ('faculty', 'group', 'enrollment_year')
    search_fields = ('user__full_name', 'user__email', 'group', 'faculty')

    def calculate_gpa(self, obj):
        return obj.calculate_gpa()
    calculate_gpa.short_description = 'GPA'

    def is_at_risk(self, obj):
        return obj.is_at_risk()
    is_at_risk.boolean = True
    is_at_risk.short_description = 'At Risk?'


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'credit', 'teacher', 'get_average_score', 'get_pass_rate')
    list_filter = ('credit',)
    search_fields = ('name', 'teacher__user__full_name')

    def get_average_score(self, obj):
        return f'{obj.get_average_score():.1f}'
    get_average_score.short_description = 'Avg Score'

    def get_pass_rate(self, obj):
        return f'{obj.get_pass_rate():.1f}%'
    get_pass_rate.short_description = 'Pass Rate'


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'midterm', 'final', 'attendance', 'total_score', 'get_letter_grade')
    list_filter = ('subject',)
    search_fields = ('student__user__full_name', 'subject__name')
    readonly_fields = ('total_score',)

    def get_letter_grade(self, obj):
        return obj.get_letter_grade()
    get_letter_grade.short_description = 'Grade'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'percentage', 'recorded_at')
    list_filter = ('subject',)
    search_fields = ('student__user__full_name', 'subject__name')

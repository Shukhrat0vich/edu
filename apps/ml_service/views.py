"""ML Service views — prediction endpoint and model info."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View

from .ml_model import grade_predictor


@method_decorator(login_required, name='dispatch')
class PredictionView(View):
    """Interactive prediction form view."""
    template_name = 'dashboard/prediction.html'

    def get(self, request):
        model_info = grade_predictor.get_model_info()
        context = {'model_info': model_info, 'prediction': None}

        # Prefill for students using their actual grade data
        if request.user.is_student:
            try:
                student = request.user.student_profile
                grades = student.grades.all()
                if grades.exists():
                    import numpy as np
                    avg_attendance = float(np.mean([g.attendance for g in grades]))
                    avg_midterm = float(np.mean([g.midterm for g in grades]))
                    gpa = student.calculate_gpa()
                    context['prefill'] = {
                        'attendance': round(avg_attendance, 1),
                        'midterm': round(avg_midterm, 1),
                        'previous_gpa': gpa,
                    }
            except Exception:
                pass

        return render(request, self.template_name, context)

    def post(self, request):
        is_ajax = request.POST.get('ajax') == '1'
        model_info = grade_predictor.get_model_info()

        try:
            attendance = float(request.POST.get('attendance', 0))
            midterm = float(request.POST.get('midterm', 0))
            previous_gpa = float(request.POST.get('previous_gpa', 2.5))

            if not grade_predictor.is_ready():
                if is_ajax:
                    return JsonResponse({'error': 'ML model not trained yet.'}, status=400)
                context = {'model_info': model_info, 'error': 'ML model not trained yet.'}
                return render(request, self.template_name, context)

            result = grade_predictor.predict(attendance, midterm, previous_gpa)

            if is_ajax:
                return JsonResponse(result)

            context = {
                'model_info': model_info,
                'prediction': result,
                'prefill': {
                    'attendance': attendance,
                    'midterm': midterm,
                    'previous_gpa': previous_gpa,
                },
            }
        except ValueError as e:
            if is_ajax:
                return JsonResponse({'error': str(e)}, status=400)
            context = {'model_info': model_info, 'error': f'Invalid input: {e}'}

        return render(request, self.template_name, context)

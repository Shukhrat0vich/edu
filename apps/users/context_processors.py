"""Context processors for user role information in templates."""


def user_role(request):
    """Inject user role info into all template contexts."""
    if request.user.is_authenticated:
        return {
            'user_role': request.user.role,
            'is_admin': request.user.role == 'ADMIN',
            'is_teacher': request.user.role == 'TEACHER',
            'is_student': request.user.role == 'STUDENT',
        }
    return {'user_role': None, 'is_admin': False, 'is_teacher': False, 'is_student': False}

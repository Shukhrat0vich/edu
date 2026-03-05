"""
Role-based access control middleware.
Restricts access to certain URL prefixes based on user role.
"""
from django.shortcuts import redirect
from django.conf import settings


class RoleBasedAccessMiddleware:
    """
    Middleware to enforce role-based access control on URL level.
    Works alongside view-level decorators for defence in depth.
    """

    # URL prefixes that are public (no authentication required)
    PUBLIC_URLS = ['/login/', '/api/login/', '/api/token/', '/static/', '/media/', '/admin/']

    # URL prefixes restricted per role
    ROLE_RESTRICTIONS = {
        'ADMIN': [],          # admin can access everything
        'TEACHER': ['/admin/dashboard/admin'],
        'STUDENT': ['/admin/dashboard/admin', '/dashboard/teacher', '/analytics/manage'],
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Allow public URLs
        if any(path.startswith(url) for url in self.PUBLIC_URLS):
            return self.get_response(request)

        # Redirect unauthenticated users to login
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL + f'?next={path}')

        return self.get_response(request)

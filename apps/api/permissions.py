"""Custom DRF permissions for role-based access control."""
from rest_framework.permissions import BasePermission
from apps.users.models import UserRole


class IsAdminOnly(BasePermission):
    """Only ADMIN users can access."""
    message = 'Access restricted to administrators only.'

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == UserRole.ADMIN


class IsAdminOrTeacher(BasePermission):
    """ADMIN and TEACHER users can access."""
    message = 'Access restricted to administrators and teachers.'

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [UserRole.ADMIN, UserRole.TEACHER]


class IsOwnerOrAdmin(BasePermission):
    """Allow if user owns the object or is ADMIN."""
    message = 'You can only access your own data.'

    def has_object_permission(self, request, view, obj):
        if request.user.role == UserRole.ADMIN:
            return True
        # For Student/Teacher objects, check user ownership
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'student'):
            return obj.student.user == request.user
        return False

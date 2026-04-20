from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission, IsAuthenticated


class IsAdminGroup(BasePermission):
    """
    Grants access only to authenticated users who belong to the 'Admin' group.
    Used for operations that create, modify, or delete resources.
    """

    message = "You must be an Admin to perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.groups.filter(name="Admin").exists()
        )


class IsDoctorGroup(BasePermission):
    """
    Grants access only to authenticated users who belong to the 'Doctor' group.
    """

    message = "You must be a Doctor to perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.groups.filter(name="Doctor").exists()
        )


class IsPatientGroup(BasePermission):
    """
    Grants access only to authenticated users who belong to the 'Patient' group.
    """

    message = "You must be a Patient to perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.groups.filter(name="Patient").exists()
        )


class IsAdminOrReadOnly(BasePermission):
    """
    Full access for Admin users.
    Read-only access (GET, HEAD, OPTIONS) for everyone else, including
    unauthenticated requests.

    * For public listing/detail endpoints that only Admins can modify.
    """

    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        
        if not request.user or not request.user.is_authenticated:
            raise AuthenticationFailed("Authentication credentials were not provided or token has expired.")
        
        return request.user.groups.filter(name="Admin").exists() or request.user.is_superuser
from rest_framework.permissions import BasePermission


class HasRole(BasePermission):
    allowed_roles = set()

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in self.allowed_roles)


class IsAdminRole(HasRole):
    allowed_roles = {'admin'}


class IsFlightOpsOrAdmin(HasRole):
    allowed_roles = {'admin', 'flight_ops'}


class IsMaintenanceOrAdmin(HasRole):
    allowed_roles = {'admin', 'maintenance'}


class IsCommanderAuditorOrAdmin(HasRole):
    allowed_roles = {'admin', 'commander', 'auditor'}

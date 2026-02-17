from rest_framework.permissions import BasePermission, SAFE_METHODS
from apps.accounts.models import UserRole


# ------------------------------------------------------------
# Role helpers
# ------------------------------------------------------------

def user_role_codes(user):
    if not user or not user.is_authenticated:
        return []
    return list(UserRole.objects.filter(user=user).values_list("role__code", flat=True))


def has_role(user, *codes: str) -> bool:
    roles = set(user_role_codes(user))
    return any(c in roles for c in codes)


SUPERVISOR_ROLES = {
    "BAC_HEAD", "BRC_HEAD",
    "REGIONAL_MANAGER", "DEPUTY_REGIONAL_MANAGER",
    "DIRECTOR_ADMIN", "DIRECTOR_FINANCE", "DIRECTOR_WEDD", "DIRECTOR_FSSD", "DIRECTOR_PPRMED",
    "DIRECTOR_HR", "DIRECTOR_MSID", "DEPUTY_DIRECTOR_MSID", "DIRECTOR_MSME", "DEPUTY_DIRECTOR_MSME",
    "AUDIT_HEAD", "PR_HEAD",
}


# ------------------------------------------------------------
# Permissions
# ------------------------------------------------------------

class IsSystemAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and has_role(request.user, "SYSTEM_ADMIN")


class IsHRorCEOReadOnly(BasePermission):
    """
    HR + CEO can view everything but cannot edit anything.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.method in SAFE_METHODS and has_role(request.user, "HR_HO", "CEO", "DIRECTOR_HR")


class IsSupervisor(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        roles = set(user_role_codes(request.user))
        return bool(roles.intersection(SUPERVISOR_ROLES))


class IsAdminOrReadOnlyHRCEOOrSupervisor(BasePermission):
    """
    - SYSTEM_ADMIN: full access
    - HR/CEO/DIRECTOR_HR: read-only
    - Supervisors: allowed (scope is enforced by queryset filtering + workflow rules)
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Admin: full access
        if has_role(request.user, "SYSTEM_ADMIN"):
            return True

        # HR/CEO: read-only
        if request.method in SAFE_METHODS and has_role(request.user, "HR_HO", "CEO", "DIRECTOR_HR"):
            return True

        # Supervisors: access allowed, scope enforced elsewhere
        roles = set(user_role_codes(request.user))
        if roles.intersection(SUPERVISOR_ROLES):
            return True

        return False


# ------------------------------------------------------------
# Query Scoping Mixin
# ------------------------------------------------------------

class RegionScopedQueryMixin:
    """
    Scopes queryset by user's allowed regions unless user is HO-level.

    Assumes:
    - ViewSet defines: region_field = "employee__employments__region"
    - HO roles can see all regions:
      SYSTEM_ADMIN, CEO, HR_HO, DIRECTOR_HR
    - Otherwise:
      if user has an employee record + ACTIVE employment => limit to that region
    """

    HO_ROLES = {"SYSTEM_ADMIN", "CEO", "HR_HO", "DIRECTOR_HR"}

    def scope_queryset(self, qs, request):
        user = request.user
        if not user or not user.is_authenticated:
            return qs.none()

        roles = set(user_role_codes(user))
        if roles.intersection(self.HO_ROLES):
            return qs

        region_field = getattr(self, "region_field", None)
        if not region_field:
            return qs.none()

        employee = getattr(user, "employee", None)
        if not employee:
            return qs.none()

        active = (
            employee.employments.filter(status="ACTIVE")
            .order_by("-created_at")
            .first()
        )
        if not active or not active.region_id:
            return qs.none()

        # NOTE: region_field typically points to a FK field, so compare by id safely.
        return qs.filter(**{f"{region_field}__id": active.region_id})


# ------------------------------------------------------------
# Backward compatibility (older modules still import this)
# ------------------------------------------------------------

class IsHROrManagement(IsAdminOrReadOnlyHRCEOOrSupervisor):
    """
    Compatibility alias for older modules importing IsHROrManagement.
    """
    pass

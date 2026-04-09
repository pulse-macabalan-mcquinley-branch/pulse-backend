from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwner(BasePermission):
    """
    Object-level: only the resource owner may write.
    Model must have a 'user' FK or 'owner' FK pointing to the user.
    """

    owner_field = "user"  # Override per ViewSet if needed

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        owner = getattr(obj, self.owner_field, None)
        return owner == request.user


class IsAdminOrReadOnly(BasePermission):
    """Read is public; write requires admin role."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_staff


class IsSuperAdmin(BasePermission):
    """Superadmin-only access."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "superadmin"


class RolePermission(BasePermission):
    """
    Declarative role-based permission. Set 'required_roles' on the view.

    Usage on a ViewSet:
        class UserViewSet(ModelViewSet):
            required_roles = {
                "list":    ["admin", "superadmin"],
                "create":  ["admin", "superadmin"],
                "destroy": ["superadmin"],
            }
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        required_roles = getattr(view, "required_roles", None)
        if not required_roles:
            return True

        action = getattr(view, "action", None)
        roles_for_action = required_roles.get(action)

        if roles_for_action is None:
            return True  # Not restricted

        return request.user.role in roles_for_action


class IsOwnerOrAdmin(BasePermission):
    """Owner can write to their own resource; admins can write to any."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.role in ("admin", "superadmin"):
            return True
        owner = getattr(obj, "user", None) or getattr(obj, "owner", None)
        return owner == request.user
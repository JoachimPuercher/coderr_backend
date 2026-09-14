from rest_framework.permissions import BasePermission, SAFE_METHODS


class ProfileDetailPermission(BasePermission):
    """Everyone may read a profile, only its owner may change it."""

    message = "You have no permission to change that profile."

    def has_object_permission(self, request, view, obj):
        """Runs after get_object(), so a missing profile answers 404 first."""
        if request.method in SAFE_METHODS:
            return True

        else:
            if obj.user_id == request.user.id:
                return True

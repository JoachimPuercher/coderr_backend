from rest_framework.permissions import BasePermission


class IsBusinessUser(BasePermission):
    """Only accounts with a business profile may create offers."""

    def has_permission(self, request, view):
        """Runs for every request, before any object is loaded."""
        self.message = (
            "You are not allowed, only business user can create offers."
        )

        # getattr with a default also covers
        # AnonymousUser and users without a profile
        profile = getattr(request.user, 'userprofile', None)
        if profile is not None and profile.type == 'business':
            return True

        return False


class IsOfferCreator(BasePermission):
    """An offer may only be edited or deleted by the user who created it."""

    def has_object_permission(self, request, view, obj):
        """Runs after get_object(), so a missing offer answers 404 first."""
        self.message = "No permissions to change that offer."

        if obj.user == request.user:
            return True

        return False

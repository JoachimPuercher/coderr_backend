from rest_framework.permissions import BasePermission


class IsReviewOwner(BasePermission):
    """A review may only be edited or deleted by its author."""

    def has_object_permission(self, request, view, obj):
        """Runs after get_object(), so a missing review answers 404 first."""
        self.message = "Only owner of the review can edit."

        if request.user == obj.reviewer:
            return True
        else:
            return False

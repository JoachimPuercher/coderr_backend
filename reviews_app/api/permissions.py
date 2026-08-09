from rest_framework.permissions import BasePermission


class IsReviewOwner(BasePermission):
    """A review may only be edited or deleted by its author."""

    def has_object_permission(self, request, view, obj):

        self.message = "Only owner of the review can edit."
        print(f"USER", request.user)
        print(f"REV", obj.reviewer)
        if request.user == obj.reviewer:
            return True
        else:
            return False

from rest_framework.permissions import BasePermission


class IsReviewOwner(BasePermission):

    def has_object_permission(self, request, view, obj):

        self.message = "Only owner of the review can edit."
        print(f"USER", request.user)
        print(f"REV", obj.reviewer)
        if request.user == obj.reviewer:
            return True
        else:
            return False
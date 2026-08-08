from rest_framework.permissions import BasePermission


class IsCustomer(BasePermission):

    def has_permission(self, request, view):

        self.message = "You are not a customer of coderr."

        profile = getattr(request.user, "userprofile", None)
        return profile is not None and profile.type == "customer"
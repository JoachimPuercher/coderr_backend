from rest_framework.permissions import BasePermission


class IsCustomer(BasePermission):
    """Only accounts with a customer profile pass."""

    def has_permission(self, request, view):
        self.message = "You are not a customer of coderr."

        # getattr with a default also covers AnonymousUser and users without a profile
        profile = getattr(request.user, "userprofile", None)
        return profile is not None and profile.type == "customer"


class IsBusinessUser(BasePermission):
    """Only accounts with a business profile pass."""

    def has_permission(self, request, view):
        self.message = "You are not a business user of coderr."

        profile = getattr(request.user, "userprofile", None)
        return profile is not None and profile.type == "business"


class IsOrderProvider(BasePermission):
    """An order may only be changed by the business user it was placed with."""

    def has_object_permission(self, request, view, obj):
        self.message = "Only the provider of this order can change it."

        return obj.business_user == request.user

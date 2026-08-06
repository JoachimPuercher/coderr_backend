from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission
from rest_framework.permissions import SAFE_METHODS


class IsBussinesUser(BasePermission):

    def has_permission(self, request, view):

        if request.method in SAFE_METHODS:
            return True

        if request.user.userprofile.type == 'business_user':
            self.message = "You are not allowed, only business user can create offers."
            return True

        return False
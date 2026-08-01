from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission
from rest_framework.permissions import SAFE_METHODS


class IsBussinesUser(BasePermission):

    message = "You are not allowed, only business user can create offers."

    def has_permission(self, request, view):

        if request.user.userprofile.type == 'business_user':
            return True
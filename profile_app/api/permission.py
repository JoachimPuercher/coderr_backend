from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission
from rest_framework.permissions import SAFE_METHODS


class ProfileDetailPermission(BasePermission):

    message = "You have no permission to change that profile."

    def has_object_permission(self, request, view, obj):

        if request.method in SAFE_METHODS:
            return True

        else:
            if obj.user_id == request.user.id:
                return True
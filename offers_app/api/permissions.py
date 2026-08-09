from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission
from rest_framework.permissions import SAFE_METHODS


class IsBusinessUser(BasePermission):

    def has_permission(self, request, view):

        self.message = "You are not allowed, only business user can create offers."

        if request.user.userprofile.type == 'business_user':
            
            return True

        return False


class IsOfferCreator(BasePermission):

    def has_object_permission(self, request, view, obj):

        self.message = "No permissions to change that offer."

        if obj.user == request.user:
            return True

        return False
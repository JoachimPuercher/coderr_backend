from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle

from auth_app.models import UserProfile

from .permission import ProfileDetailPermission
from .serializers import ProfilSerializer, BusinessProfilSerializer, CustomerProfilSerializer
from .throttles import ProfileUpdateRateThrottle


class ProfileView(generics.RetrieveUpdateAPIView):
    """Single profile: readable for every logged in user, editable only by its owner."""

    serializer_class = ProfilSerializer
    queryset = UserProfile.objects.all()
    permission_classes = [IsAuthenticated, ProfileDetailPermission]
    throttle_classes = [UserRateThrottle, ProfileUpdateRateThrottle]
    # the url carries the id of the USER, not of the profile row
    lookup_field = "user_id"
    lookup_url_kwarg = "pk"
    # the spec only allows partial updates, so PUT answers 405 instead of 200
    http_method_names = ["get", "patch", "options"]

class BusinessProfileView(generics.ListAPIView):
    """All business profiles, used by the provider overview in the frontend."""

    queryset = UserProfile.objects.filter(type="business")
    serializer_class = BusinessProfilSerializer


class CustomerProfileView(generics.ListAPIView):
    """All customer profiles."""

    queryset = UserProfile.objects.filter(type="customer")
    serializer_class = CustomerProfilSerializer

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from auth_app.models import UserProfile

from .permission import ProfileDetailPermission
from .serializers import ProfilSerializer, BusinessProfilSerializer, CustomerProfilSerializer


class ProfileView(generics.RetrieveUpdateAPIView):
    """Single profile: readable for every logged in user, editable only by its owner."""

    serializer_class = ProfilSerializer
    queryset = UserProfile.objects.all()
    permission_classes = [IsAuthenticated, ProfileDetailPermission]
    # the url carries the id of the USER, not of the profile row
    lookup_field = "user_id"
    lookup_url_kwarg = "pk"


class BusinessProfileView(generics.ListAPIView):
    """All business profiles, used by the provider overview in the frontend."""

    queryset = UserProfile.objects.filter(type="business")
    serializer_class = BusinessProfilSerializer


class CustomerProfileView(generics.ListAPIView):
    """All customer profiles."""

    queryset = UserProfile.objects.filter(type="customer")
    serializer_class = CustomerProfilSerializer

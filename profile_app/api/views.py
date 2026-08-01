from rest_framework import generics
from .serializers import ProfilSerializer
from auth_app.models import UserProfile
from rest_framework.permissions import AllowAny, SAFE_METHODS, IsAuthenticated
from .permission import ProfileDetailPermission
from .serializers import BusinessProfilSerializer, CustomerProfilSerializer

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfilSerializer
    queryset = UserProfile.objects.all()
    permission_classes = [IsAuthenticated, ProfileDetailPermission]


class BusinessProfileView(generics.ListAPIView):
    queryset = UserProfile.objects.filter(type="business_user")
    serializer_class = BusinessProfilSerializer

class CustomerProfileView(generics.ListAPIView):
    queryset = UserProfile.objects.filter(type="customer")
    serializer_class = CustomerProfilSerializer
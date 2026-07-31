from rest_framework import generics
from .serializers import ProfilSerializer
from auth_app.models import UserProfile
from rest_framework.permissions import AllowAny, SAFE_METHODS, IsAuthenticated
from .permission import ProfileDetailPermission

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfilSerializer
    queryset = UserProfile.objects.all()
    permission_classes = [IsAuthenticated, ProfileDetailPermission]

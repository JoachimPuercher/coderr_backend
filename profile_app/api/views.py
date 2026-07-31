from rest_framework import generics
from .serializers import ProfilSerializer
from auth_app.models import UserProfile
from rest_framework.permissions import AllowAny, SAFE_METHODS

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfilSerializer
    queryset = UserProfile.objects.all()
    

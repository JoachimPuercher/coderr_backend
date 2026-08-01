from rest_framework import generics
from rest_framework.permissions import AllowAny, SAFE_METHODS, IsAuthenticated
from .serializers import OfferMainSerializer
from .permissions import IsBussinesUser

class OfferMainView(generics.ListCreateAPIView):
    serializer_class = OfferMainSerializer
    permission_classes = [IsAuthenticated, IsBussinesUser]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
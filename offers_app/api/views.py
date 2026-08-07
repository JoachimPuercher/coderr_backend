from rest_framework import generics
from rest_framework.permissions import AllowAny, SAFE_METHODS, IsAuthenticated
from rest_framework.filters import SearchFilter
from .serializers import OfferMainSerializer
from .permissions import IsBussinesUser
from offers_app.models import Offer
from django_filters.rest_framework import DjangoFilterBackend
from .filters import OfferFilter

class OfferMainView(generics.ListCreateAPIView):
    serializer_class = OfferMainSerializer
    queryset = Offer.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = OfferFilter
    search_fields = ["title", "description"]
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_permissions(self):
                if self.request.method in SAFE_METHODS:
                    return [AllowAny()]
                else:
                    return [IsAuthenticated(), IsBussinesUser()]

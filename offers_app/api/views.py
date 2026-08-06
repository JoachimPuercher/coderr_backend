from rest_framework import generics
from rest_framework.permissions import AllowAny, SAFE_METHODS, IsAuthenticatedOrReadOnly
from .serializers import OfferMainSerializer
from .permissions import IsBussinesUser
from offers_app.models import Offer
from django_filters.rest_framework import DjangoFilterBackend
from .filters import OfferFilter

class OfferMainView(generics.ListCreateAPIView):
    serializer_class = OfferMainSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsBussinesUser]
    queryset = Offer.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = OfferFilter

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
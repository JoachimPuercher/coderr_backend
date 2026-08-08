from rest_framework import generics
from rest_framework.permissions import AllowAny, SAFE_METHODS, IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from .serializers import OfferWriteSerializer, OfferListSerializer
from .permissions import IsBussinesUser
from offers_app.models import Offer
from django_filters.rest_framework import DjangoFilterBackend
from .filters import OfferFilter
from .pagination import OfferPagination

class OfferListCreateView(generics.ListCreateAPIView):
    queryset = Offer.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = OfferFilter
    search_fields = ["title", "description"]
    ordering_fields = ["updated_at", "min_price"]
    pagination_class = OfferPagination

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_permissions(self):
            if self.request.method in SAFE_METHODS:
                return [AllowAny()]
            else:
                return [IsAuthenticated(), IsBussinesUser()]

    def get_serializer_class(self):
          if self.request.method == "POST":
               return OfferWriteSerializer
          return OfferListSerializer
from rest_framework import generics
from rest_framework.permissions import AllowAny, SAFE_METHODS, IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from .serializers import OfferWriteSerializer, OfferListSerializer, OfferRetrieveSerializer, OfferDetailSerializer
from .permissions import IsBusinessUser, IsOfferCreator
from offers_app.models import Offer, OfferDetail
from django.db.models import Min
from django_filters.rest_framework import DjangoFilterBackend
from .filters import OfferFilter
from .pagination import OfferPagination

class OfferListCreateView(generics.ListCreateAPIView):
    """Public offer list with search, filters and paging; only business users may post."""

    # the two minimums are computed by the database so they stay filterable and sortable
    queryset = Offer.objects.annotate(
        min_price=Min("details__price"),
        min_delivery_time=Min("details__delivery_time_in_days"),
    )
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = OfferFilter
    search_fields = ["title", "description"]
    ordering_fields = ["updated_at", "min_price"]
    pagination_class = OfferPagination

    def perform_create(self, serializer):
        # the creator comes from the token, never from the payload
        serializer.save(user=self.request.user)

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        else:
            return [IsAuthenticated(), IsBusinessUser()]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OfferWriteSerializer
        return OfferListSerializer


class OfferDetailRetrieveView(generics.RetrieveAPIView):
    """Single package, linked from the details list of an offer."""

    queryset = OfferDetail.objects.all()
    lookup_url_kwarg = "id"
    serializer_class = OfferDetailSerializer


class OfferSingleView(generics.RetrieveUpdateDestroyAPIView):
    """Read, edit or delete one offer. Editing is limited to its creator."""

    queryset = Offer.objects.annotate(
        min_price=Min("details__price"),
        min_delivery_time=Min("details__delivery_time_in_days"),
    )
    lookup_url_kwarg = "id"
    # the parent class would also offer PUT, which the API does not support
    http_method_names = ["get", "patch", "delete", "options"]

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return OfferRetrieveSerializer

        return OfferWriteSerializer

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated()]

        if self.request.method == "PATCH":
            return [IsAuthenticated(), IsOfferCreator()]

        if self.request.method == "DELETE":
            return [IsAuthenticated(), IsOfferCreator()]

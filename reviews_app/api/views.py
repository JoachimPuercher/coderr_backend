from rest_framework import generics
from reviews_app.models import Review
from .serializers import ReviewSerializer
from rest_framework.permissions import AllowAny, SAFE_METHODS, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .filters import ReviewFilter
from orders_app.api.permissions import IsCustomer

class ReviewListCreateView(generics.ListCreateAPIView):

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    filter_backends = [OrderingFilter, DjangoFilterBackend]
    filterset_class = ReviewFilter
    ordering_fields = ["updated_at", "rating"]

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated()]

        if self.request.method == "POST":
            return [IsAuthenticated(), IsCustomer()]